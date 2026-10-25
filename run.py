import os
import sys
from pathlib import Path
import uvicorn

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    # Bind to 0.0.0.0 so Docker container port mapping works
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
    aris.com",
        password: str = "Zetaris1@",
    ):
        self.host = host or os.getenv("ZETARIS_HOST", "127.0.0.1")
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"http://{self.host}:{self.port}"
        self._auth_token: Optional[str] = None

    async def authenticate(self) -> bool:
        """Authenticate with Zetaris REST API (Port 8888)."""
        if getattr(settings, "SAMPLE_MODE", False):
            return True

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={"username": self.username, "password": self.password},
                )
                if res.status_code == 200:
                    self._auth_token = res.json().get("token")
                    return True
        except Exception as e:
            logger.debug(f"[Zetaris Client] Local cluster probe ({self.base_url}): {e}")
        return False

    async def execute_federated_query(self, query: str) -> Dict[str, Any]:
        """
        Executes a zero-copy federated query via Zetaris Lightning Engine.
        Falls back to local verified structure if cluster is offline.
        """
        t0 = time.perf_counter()

        if self._auth_token:
            try:    # Bind to 0.0.0.0 so Docker container port mapping works
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)