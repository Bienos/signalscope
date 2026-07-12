const base=process.env.API_URL||process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000';
async function auth(){const body=new URLSearchParams({username:'admin@viralradar.local',password:'RadarDemo!2026'});const r=await fetch(base+'/api/auth/token',{method:'POST',body,cache:'no-store'});if(!r.ok)return '';return (await r.json()).access_token as string}
export async function api<T>(path:string,fallback:T):Promise<T>{try{const t=await auth();const r=await fetch(base+path,{headers:{Authorization:`Bearer ${t}`},cache:'no-store'});return r.ok?await r.json():fallback}catch{return fallback}}

