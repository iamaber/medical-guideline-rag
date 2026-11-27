'use client';

import { useEffect, useEffectEvent, type RefObject } from 'react';

/**
 * Text typed or an option chosen before React hydrates stays on screen while state keeps its
 * initial value, so the form would show input it never submits. Once mounted, pass each field's
 * on-screen value to `adopt` so state matches what the user sees.
 */
export function useAdoptPreHydrationInput(
  formRef: RefObject<HTMLFormElement | null>,
  adopt: (id: string, value: string) => void
): void {
  const adoptField = useEffectEvent(adopt);

  useEffect(() => {
    for (const field of Array.from(formRef.current?.elements ?? [])) {
      if ((field instanceof HTMLInputElement || field instanceof HTMLSelectElement) && field.id) {
        adoptField(field.id, field.value);
      }
    }
  }, [formRef]);
}
