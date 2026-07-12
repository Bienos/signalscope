import {NextRequest,NextResponse} from 'next/server';
const base=process.env.API_URL||'http://api:8000';
async function token(){const body=new URLSearchParams({username:'admin@viralradar.local',password:'RadarDemo!2026'});const r=await fetch(base+'/api/auth/token',{method:'POST',body,cache:'no-store'});return (await r.json()).access_token as string}
export async function POST(request:NextRequest,{params}:{params:Promise<{id:string}>}){try{const {id}=await params;const value=await request.json() as {useful?:boolean;note?:string};const query=new URLSearchParams();if(value.useful!==undefined)query.set('useful',String(value.useful));if(value.note)query.set('note',value.note);const t=await token();const r=await fetch(`${base}/api/reports/${id}/review?${query}`,{method:'POST',headers:{Authorization:`Bearer ${t}`},cache:'no-store'});return NextResponse.json(await r.json(),{status:r.status})}catch{return NextResponse.json({detail:'Review service unavailable'},{status:503})}}

