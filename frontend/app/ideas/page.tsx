import IdeaWorkspace from '../../components/IdeaWorkspace';
import {FeatureGate} from '../../components/FeatureGate';
export const metadata={title:'Ideas'};export default function Page(){return <FeatureGate feature="ideas" title="Create original content opportunities" plan="SignalScope Pro"><IdeaWorkspace/></FeatureGate>}
