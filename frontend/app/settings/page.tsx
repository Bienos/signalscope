import {api} from '../lib';
import SettingsDemo from '../../components/SettingsDemo';
export default async function Page(){const capabilities=await api<any>('/api/provider-capabilities',{provider:'Unavailable',mode:'Unavailable',capabilities:[]});return <SettingsDemo capabilities={capabilities}/>}
