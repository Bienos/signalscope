'use client';
import {createContext,useContext,useState} from 'react';import {AddOnId,canUse,FeatureId,PlanId} from '../lib/commercial';
type Ctx={plan:PlanId;addons:AddOnId[];setPlan:(x:PlanId)=>void;toggleAddon:(x:AddOnId)=>void;allowed:(x:FeatureId)=>boolean};
const CommercialContext=createContext<Ctx|null>(null);
export function CommercialProvider({children}:{children:React.ReactNode}){const [plan,setPlanState]=useState<PlanId>('free');const [addons,setAddons]=useState<AddOnId[]>([]);const setPlan=(x:PlanId)=>setPlanState(x);const toggleAddon=(x:AddOnId)=>setAddons(current=>current.includes(x)?current.filter(a=>a!==x):[...current,x]);return <CommercialContext.Provider value={{plan,addons,setPlan,toggleAddon,allowed:f=>canUse(plan,addons,f)}}>{children}</CommercialContext.Provider>}
export function useCommercial(){const value=useContext(CommercialContext);if(!value)throw new Error('CommercialProvider missing');return value}
