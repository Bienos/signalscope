import {NextResponse} from 'next/server';
const base=process.env.API_URL||'http://api:8000';
async function token(){const body=new URLSearchParams({username:'admin@viralradar.local',password:'RadarDemo!2026'});const r=await fetch(base+'/api/auth/token',{method:'POST',body,cache:'no-store'});return (await r.json()).access_token as string}
export async function POST(){try{const t=await token();const r=await fetch(base+'/api/reports/generate',{method:'POST',headers:{Authorization:`Bearer ${t}`},cache:'no-store'});return NextResponse.json(await r.json(),{status:r.status})}catch{return NextResponse.json({detail:'Report service unavailable'},{status:503})}}

