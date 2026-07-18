import Image from 'next/image';

type BrandLogoProps = {
  variant: 'on-dark' | 'on-light';
  className?: string;
  priority?: boolean;
  sizes?: string;
};

const sources = {
  'on-dark': '/brand/signalscope-wordmark-on-dark.png',
  'on-light': '/brand/signalscope-wordmark-on-light.png',
} as const;

export function BrandLogo({
  variant,
  className,
  priority = false,
  sizes = '210px',
}: BrandLogoProps) {
  return <Image
    src={sources[variant]}
    width={520}
    height={150}
    sizes={sizes}
    className={className}
    alt=""
    aria-hidden="true"
    priority={priority}
  />;
}
