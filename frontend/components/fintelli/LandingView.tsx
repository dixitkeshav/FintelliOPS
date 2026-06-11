'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { LANDING_HTML } from './landing-html';

export function LandingView() {
  const router = useRouter();

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      const nav = t.closest('[data-nav]') as HTMLElement | null;
      if (nav) {
        const href = nav.getAttribute('data-nav');
        if (href) {
          e.preventDefault();
          router.push(href);
        }
        return;
      }
      const faqQ = t.closest('.faq-q');
      if (faqQ?.parentElement) faqQ.parentElement.classList.toggle('open');
    };
    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  }, [router]);

  return <div dangerouslySetInnerHTML={{ __html: LANDING_HTML }} />;
}
