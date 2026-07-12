import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import ProviderVideo
class GenericRestProvider:
    """Configuration-only adapter. Endpoint and mapping require licensed vendor documentation."""
    def __init__(self,base_url:str,auth_header:str,token:str,mapping:dict): self.base_url=base_url; self.auth_header=auth_header; self._token=token; self.mapping=mapping
    @retry(stop=stop_after_attempt(3),wait=wait_exponential(max=8))
    def _request(self,path:str):
        if not path: raise ValueError("Vendor-documented endpoint path is required")
        with httpx.Client(base_url=self.base_url,timeout=20) as c: return c.get(path,headers={self.auth_header:self._token}).raise_for_status().json()
    def discover_videos(self)->list[ProviderVideo]: raise NotImplementedError("Configure documented vendor mapping before use")
    def health_check(self): return {"ok":bool(self.base_url),"provider":"generic_rest"}

