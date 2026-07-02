---
name: gsap-animation
description: Guides implementing premium web animations using GSAP and ScrollTrigger in Next.js/React applications.
---

# gsap-animation (Premium Web Motion)

This skill governs implementing motion design. Standard CSS transitions often look linear and artificial. Use GSAP (GreenSock Animation Platform) to achieve natural, physics-based movement.

## Next.js / React Setup

Always use the official `@gsap/react` package to manage component lifecycle automatically and prevent memory leaks.

```tsx
import { useRef } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Register plugins globally
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger, useGSAP);
}

export default function MyComponent() {
  const container = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    // GSAP animations go here.
    // They are automatically cleaned up when the component unmounts.
    gsap.from('.box', { 
      opacity: 0, 
      y: 50, 
      duration: 1, 
      stagger: 0.2,
      ease: 'power3.out' 
    });
  }, { scope: container }); // Scoping prevents targeting global classes

  return (
    <div ref={container}>
      <div className="box">Item 1</div>
      <div className="box">Item 2</div>
    </div>
  );
}
```

---

## Animation Patterns

### 1. Scroll Reveal (Плавное появление при скролле)
Never use boring, synchronized scroll reveals. Use staggered entry with proper ease and physics.
*   **Ease**: `power3.out` or `expo.out` (never `linear` or `power1.inOut`).
*   **Stagger**: Add minor delay between elements (`stagger: 0.1` or `0.15`).
*   **Code Template**:
    ```typescript
    gsap.from('.reveal-item', {
      scrollTrigger: {
        trigger: '.reveal-container',
        start: 'top 80%', // starts when top of container hits 80% viewport height
        toggleActions: 'play none none reverse'
      },
      y: 60,
      opacity: 0,
      duration: 1.2,
      ease: 'power4.out',
      stagger: 0.15
    });
    ```

### 2. Parallax Effect (Эффект параллакса)
Smooth background/element displacement tied directly to the scrollbar position.
*   **Scrub**: Bind motion speed to scrollbar (`scrub: true` or `scrub: 1` for a smooth catch-up).
*   **Code Template**:
    ```typescript
    gsap.to('.parallax-bg', {
      scrollTrigger: {
        trigger: '.parallax-section',
        start: 'top bottom',
        end: 'bottom top',
        scrub: 1
      },
      yPercent: -20, // Shifts background upwards as you scroll down
      ease: 'none'  // Linear ease is required for scrub-based parallax
    });
    ```

### 3. Pinning & Horizontal Scroll (Закрепление и горизонтальный скролл)
Pinning sections in place while scrolling horizontally or revealing cards.
*   **Pin**: Locks the element on the screen during the scroll length.
*   **Code Template**:
    ```typescript
    const sections = gsap.utils.toArray('.panel');
    gsap.to(sections, {
      xPercent: -100 * (sections.length - 1),
      ease: 'none',
      scrollTrigger: {
        trigger: '.pin-container',
        pin: true,
        scrub: 1,
        snap: 1 / (sections.length - 1),
        start: 'top top',
        end: () => '+=' + document.querySelector('.pin-container')?.offsetWidth
      }
    });
    ```

---

## Whitelist & Blacklist

### 🚫 Blacklist (Never Use)
*   **No raw CSS animations**: Do not write `@keyframes` for scroll animations. Use GSAP.
*   **No React state for scroll tracking**: Never bind window scroll event listeners (`window.addEventListener('scroll')`) to trigger state and force re-renders. Use `ScrollTrigger` instead.
*   **No linear easing**: Never use `ease-in` or `ease-out` default CSS values. Use GSAP’s natural ease functions: `power3.out`, `back.out(1.7)`, `elastic.out`.

### ✅ Whitelist (Always Use)
*   **Scope GSAP calls**: Always pass `scope` property referencing a React `useRef` to `useGSAP`.
*   **Cleanup validation**: Verify that no orphan event listeners remain after animation.
*   **Media query compatibility**: Wrap heavy desktop animations in `gsap.matchMedia()` to disable them on mobile devices for better performance.
