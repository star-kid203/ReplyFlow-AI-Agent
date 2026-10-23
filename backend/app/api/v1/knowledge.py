# FILE: backend/app/api/v1/knowledge.py
import asyncio
import html as html_lib
import json
import logging
import re
from urllib.parse import urljoin, urlparse
import uuid
from typing import List, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, Query, status
import httpx
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.llm.factory import get_llm_provider
from app.models.entities import Business, BusinessKnowledge, Product
from app.schemas.knowledge import KnowledgeResponse

logger = logging.getLogger("replyflow.knowledge")
router = APIRouter(prefix="/knowledge", tags=["Business Knowledge & Connectors"])


class CrawlWebsiteRequest(BaseModel):
    business_id: uuid.UUID
    website_url: str = Field(..., description="Target business website to crawl and extract capabilities from")
    extract_services_to_portfolio: bool = Field(default=True)
    replace_existing_offerings: bool = Field(default=True)


class DirectTextIngestRequest(BaseModel):
    business_id: uuid.UUID
    source_title: str = Field(default="Company Documentation / Deck")
    raw_text: str = Field(..., min_length=20)
    extract_services_to_portfolio: bool = Field(default=True)
    replace_existing_offerings: bool = Field(default=False)


@router.get("", response_model=List[KnowledgeResponse])
async def list_knowledge(
    business_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    query = select(BusinessKnowledge).where(
        BusinessKnowledge.business_id == business_id,
        BusinessKnowledge.is_active.is_(True)
    )
    res = await db.execute(query)
    return list(res.scalars().all())


@router.delete("/{knowledge_id}", status_code=status.HTTP_200_OK)
async def delete_knowledge_item(
    knowledge_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = select(BusinessKnowledge).where(BusinessKnowledge.id == knowledge_id)
    res = await db.execute(query)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    await db.delete(item)
    await db.commit()
    return {"status": "success", "message": f"Deleted policy '{item.title}'"}


def clean_semantic_dom_text(html: str) -> str:
    """
    Extracts complete, uncorrupted visible text from any HTML or single-page app.
    Strips scripts, styles, SVGs, and unescapes HTML entities.
    """
    extracted_lines: List[str] = []

    # 1. Capture OpenGraph / meta descriptions
    for m in re.findall(r'<meta\s+[^>]*(?:name|property)=["\'](?:description|og:description)["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE):
        if len(m.strip()) > 15:
            extracted_lines.append(f"Company Profile: {html_lib.unescape(m.strip())}")

    # 2. Extract Next.js / Nuxt hydration payload data
    next_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    if next_match:
        try:
            next_json = json.loads(next_match.group(1))
            def walk(obj):
                if isinstance(obj, str) and 15 < len(obj.strip()) < 800 and not obj.startswith("http") and "{" not in obj:
                    extracted_lines.append(obj.strip())
                elif isinstance(obj, dict):
                    for v in obj.values():
                        walk(v)
                elif isinstance(obj, list):
                    for item in obj:
                        walk(item)
            walk(next_json)
        except Exception:
            pass

    # 3. Strip non-content blocks (scripts, styles, SVGs, noscript)
    clean_html = re.sub(r'<(script|style|svg|noscript)[^>]*>.*?</\1>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    clean_html = re.sub(r'<!--.*?-->', ' ', clean_html, flags=re.DOTALL)

    # 4. Convert all HTML tags to line breaks so cards, divs, and paragraphs remain distinct
    text_content = re.sub(r'<[^>]+>', '\n', clean_html)
    text_content = html_lib.unescape(text_content)

    for line in text_content.splitlines():
        line = " ".join(line.split())
        if (
            len(line) > 3
            and not any(css in line for css in ["--wp-", "var(--", "{", "}", ";", "display:", "margin:", "padding:", "function()", "const "])
            and not line.startswith(("http://", "https://", "©", "All rights"))
        ):
            extracted_lines.append(line)

    unique_lines = list(dict.fromkeys(extracted_lines))
    return "\n\n".join(unique_lines)


def discover_internal_capability_urls(base_url: str, raw_html: str, max_links: int = 5) -> List[str]:
    """
    Finds internal links to capability pages (services, solutions, case-studies, about, work).
    """
    parsed_base = urlparse(base_url)
    discovered: Set[str] = set()

    capability_keywords = ["service", "solution", "case-stud", "product", "practice", "about", "portfolio", "work"]
    href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)

    for href in href_pattern.findall(raw_html):
        href = href.strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        resolved = urljoin(base_url, href)
        parsed_target = urlparse(resolved)

        # Must be on the exact same domain
        if parsed_target.netloc == parsed_base.netloc:
            path_lower = parsed_target.path.lower()
            if any(kw in path_lower for kw in capability_keywords) and resolved != base_url:
                discovered.add(resolved)
                if len(discovered) >= max_links:
                    break

    return list(discovered)


async def deep_crawl_site(target_url: str) -> tuple[str, str]:
    """
    Crawls the main page and concurrently crawls relevant capability subpages
    to compile a comprehensive multi-page corporate profile.
    """
    final_url, main_html = await robust_fetch_url(target_url)
    all_text_sections = [clean_semantic_dom_text(main_html)]

    sub_urls = discover_internal_capability_urls(final_url, main_html, max_links=4)
    if sub_urls:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True, verify=False) as client:
            tasks = [client.get(u) for u in sub_urls]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for r in responses:
                if isinstance(r, httpx.Response) and r.status_code == 200 and len(r.text) > 100:
                    cleaned_sub = clean_semantic_dom_text(r.text)
                    if len(cleaned_sub) > 60:
                        all_text_sections.append(cleaned_sub)

    combined_corpus = "\n\n--- CAPABILITY SECTION ---\n\n".join(all_text_sections)
    return final_url, combined_corpus


async def extract_services_via_llm(
    business_id: uuid.UUID,
    content: str,
    source_label: str,
    replace_existing: bool,
    db: AsyncSession
) -> int:
    """
    Extracts all distinct enterprise capabilities:
    1. Core Commercial Services
    2. Turnkey Solutions & Case-Study Platforms
    3. Specialized Infrastructure & SLA Maintenance Packages
    """
    llm = get_llm_provider()

    system_prompt = (
        "You are an enterprise business intelligence analyst.\n"
        "Your mission is to perform an exhaustive, complete extraction of EVERY commercial capability, service, "
        "practice area, case-study platform, and specialized maintenance package offered by the company.\n\n"
        "EXTRACTION DIRECTIVES:\n"
        "1. EXTRACT ALL 3 TIERS OF OFFERINGS (DO NOT LUMP OR STOP AT BROAD TITLES):\n"
        "   - Tier 1: Core Service Lines (e.g. Website Development, Mobile App Development, Enterprise Software Development, Cloud Infrastructure Solutions).\n"
        "   - Tier 2: Turnkey Platforms & Case Studies (e.g. Real-Estate Marketplace App, Hospital Booking & Telehealth Suite, Corporate CMS Platform).\n"
        "   - Tier 3: Specialized Maintenance & Security Packages (e.g. 24/7 SLA Maintenance & Monitoring, Tailored Cloud Infrastructure & Cybersecurity Protection Packages, Product Strategy & UI/UX Prototyping).\n"
        "2. EXCLUDE ONLY NOISE: Do not extract generic navigation links, raw slogans, or employee names (e.g., skip 'Contact Us', 'Read More', 'Skip to content').\n"
        "3. FOR EACH OFFERING: Write a comprehensive, high-value 1-2 sentence description explaining deliverables, technical scope, and client business outcomes.\n"
        "4. Price must always be 0.00.\n\n"
        "Return a JSON object with a single key 'services' containing an array of objects:\n"
        "{\n"
        "  \"services\": [\n"
        "    {\n"
        "      \"name\": \"Distinct Capability or Solution Name\",\n"
        "      \"description\": \"Comprehensive 1-2 sentence explanation of technical deliverables and scope.\",\n"
        "      \"sku\": \"lowercase-slug-identifier\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    user_prompt = (
        f"COMPANY SOURCE: {source_label}\n\n"
        f"PAGE CONTENT:\n{content[:14000]}\n\n"
        "Perform exhaustive capability extraction across all tiers (core services, case-study platforms, maintenance packages):"
    )

    raw_ai = await llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    clean_json = raw_ai.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    items_list = []
    try:
        data = json.loads(clean_json)
        items_list = data.get("services") or data.get("offerings") or data.get("products") or list(data.values())[0]
    except Exception as parse_err:
        logger.warning(f"Standard JSON parse error: {parse_err}. Using regex fallback...")
        pattern = r'\{[^{}]*"name"\s*:\s*"([^"]+)"[^{}]*"description"\s*:\s*"([^"]+)"[^{}]*\}'
        for name, desc in re.findall(pattern, clean_json, re.DOTALL):
            items_list.append({
                "name": name.strip(),
                "description": desc.strip(),
                "sku": re.sub(r'[^a-z0-9]+', '-', name.lower().strip())
            })

    if not items_list or not isinstance(items_list, list):
        logger.info(f"AI found no distinct commercial offerings on {source_label}.")
        return 0

    if replace_existing:
        del_query = select(Product).where(Product.business_id == business_id)
        res = await db.execute(del_query)
        for old_item in res.scalars().all():
            await db.delete(old_item)

    services_added = 0
    seen_names = set()
    for s in items_list:
        if isinstance(s, dict) and s.get("name"):
            name = s.get("name").strip()
            name_clean = name.lower()
            if name_clean in seen_names or len(name) < 3:
                continue
            seen_names.add(name_clean)

            base_sku = s.get("sku", name_clean.replace(" ", "-"))
            clean_sku = re.sub(r"[^a-z0-9-]+", "", base_sku)[:70]
            unique_sku = f"{clean_sku}-{uuid.uuid4().hex[:4]}"

            description = s.get("description", "").strip()
            if not description:
                description = f"Comprehensive {name} solutions tailored to enterprise specifications."

            p = Product(
                business_id=business_id,
                sku=unique_sku,
                name=name,
                description=description,
                price=0.00,
                min_price=None,
                pricing_model="custom_quote",
                stock_quantity=99,
                metadata_info={
                    "is_custom_quote": True,
                    "pricing_model": "custom_scoping",
                    "source": source_label,
                },
            )
            db.add(p)
            services_added += 1

    await db.commit()
    logger.info(f"Successfully saved {services_added} offerings for tenant {business_id}")
    return services_added


async def robust_fetch_url(target_url: str) -> tuple[str, str]:
    candidate_urls = [target_url]
    parsed = urlparse(target_url)

    if not parsed.netloc.startswith("www."):
        candidate_urls.append(f"{parsed.scheme}://www.{parsed.netloc}{parsed.path}")
    if parsed.scheme == "https":
        candidate_urls.append(f"http://{parsed.netloc}{parsed.path}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    last_error = None
    async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True, verify=False) as client:
        for url in candidate_urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.text) > 100:
                    return url, resp.text
            except Exception as e:
                last_error = e

    raise HTTPException(
        status_code=502,
        detail=f"Could not connect to {target_url} ({last_error}). Use the 'Direct Documentation' tab to paste their company overview."
    )


@router.post("/sync/url", status_code=status.HTTP_200_OK)
async def crawl_and_extract_services_and_policies(
    payload: CrawlWebsiteRequest,
    db: AsyncSession = Depends(get_db)
):
    target_url = str(payload.website_url).strip()
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        target_url = f"https://{target_url}"

    final_url, combined_content = await deep_crawl_site(target_url)

    if len(combined_content) < 40:
        raise HTTPException(
            status_code=400,
            detail="Extracted insufficient content from page. Use the 'Direct Documentation' tab."
        )

    # 1. Save Full Multi-Page Grounding Documentation
    knowledge_entry = BusinessKnowledge(
        business_id=payload.business_id,
        category="crawled_documentation",
        title=f"Official Company Grounding ({final_url[:50]})",
        content=combined_content[:8000],
        is_active=True,
    )
    db.add(knowledge_entry)
    await db.commit()

    # 2. Extract genuine multi-tier offerings into the Portfolio
    services_added = 0
    if payload.extract_services_to_portfolio:
        services_added = await extract_services_via_llm(
            business_id=payload.business_id,
            content=combined_content,
            source_label=final_url,
            replace_existing=payload.replace_existing_offerings,
            db=db
        )

    return {
        "status": "success",
        "message": f"Successfully parsed {final_url}.",
        "services_extracted": services_added,
        "preview": combined_content[:250] + "..."
    }


@router.post("/ingest-text", status_code=status.HTTP_200_OK)
async def ingest_direct_company_text(
    payload: DirectTextIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    text = payload.raw_text.strip()

    entry = BusinessKnowledge(
        business_id=payload.business_id,
        category="company_documentation",
        title=payload.source_title,
        content=text[:6000],
        is_active=True,
    )
    db.add(entry)
    await db.commit()

    services_added = 0
    if payload.extract_services_to_portfolio:
        services_added = await extract_services_via_llm(
            business_id=payload.business_id,
            content=text,
            source_label=payload.source_title,
            replace_existing=payload.replace_existing_offerings,
            db=db
        )

    return {
        "status": "success",
        "message": f"Successfully ingested {payload.source_title}.",
        "services_extracted": services_added,
    }