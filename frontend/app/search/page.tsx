import {redirect} from 'next/navigation';
export default async function Page({searchParams}: {searchParams: Promise<{q?: string}>}) {
  const {q} = await searchParams;
  redirect(q ? `/discover?q=${encodeURIComponent(q)}` : '/discover');
}
