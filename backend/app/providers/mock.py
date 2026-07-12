import random
from datetime import datetime, timedelta, timezone
from .base import ProviderVideo

class MockProvider:
    """Deterministic licensed-provider simulator; never accesses TikTok."""
    def __init__(self, run:int=0): self.run=run
    def discover_videos(self, count:int=120)->list[ProviderVideo]:
        rng=random.Random(260711+self.run); now=datetime.now(timezone.utc).replace(tzinfo=None)
        cats=[("toy","Building sets"),("parenting","Kids activities"),("gaming","Games"),("board_game","Board games"),("general","Lifestyle"),("educational","STEM toys"),("irrelevant",None)]
        hooks=["three-step reveal","before and after test","constraint challenge","quick comparison","family reaction","unexpected use"]
        out=[]
        for i in range(count):
            cat,product=cats[i%len(cats)]; lang="pl" if i%5==0 else "en"; market=["PL","GB","US"][i%3]; age=2+(i*7)%168
            base=8_000+(i%17)*13_000; mode=i%10
            growth=180_000 if mode==0 else 45_000 if mode in (1,2) else 2_000 if mode==9 else 12_000
            views=base+growth*(self.run+1)+rng.randrange(3000); tags=["ToyTok","FamilyGameNight"] if cat in {"toy","board_game"} else ["LifeHack","Trending"]
            unsafe=i%37==0
            out.append(ProviderVideo(id=f"mock-{i:04d}",url=f"https://www.tiktok.com/@radar_creator_{i%36}/video/{7400000000000000000+i}",creator_id=f"creator-{i%36:03d}",username=f"radar_creator_{i%36}",caption=("Niebezpieczne wyzwanie" if unsafe else f"Original mock {hooks[i%len(hooks)]} for {product or cat}"),published_at=now-timedelta(hours=age),language=lang,market=market,metrics={"views":views,"likes":int(views*.08),"comments":int(views*.007),"shares":int(views*(.025 if mode<3 else .009)),"favourites":int(views*.012)},hashtags=tags,sound_id=f"sound-{i%24:03d}",sound_title=f"Observed sound {i%24+1}",provider="mock",raw_reference=f"mock://video/{i}",confidence=.95))
        return out
    def get_video_metrics(self,ids): return {v.id:v.metrics for v in self.discover_videos() if v.id in ids}
    def get_creator_profile(self,c): return {"id":c,"provider":"mock"}
    def get_creator_recent_videos(self,c): return [v for v in self.discover_videos() if v.creator_id==c]
    def discover_hashtags(self): return [{"name":f"trend{i}","growth":100-i} for i in range(48)]
    def discover_sounds(self): return [{"id":f"sound-{i:03d}","growth":90-i} for i in range(24)]
    def get_sound_videos(self,s): return [v for v in self.discover_videos() if v.sound_id==s]
    def health_check(self): return {"ok":True,"provider":"mock","freshness":"live simulation"}

