const canUseHaptics = () => {
    if (typeof window === 'undefined' || typeof navigator === 'undefined') return false;
    if (typeof navigator.vibrate !== 'function') return false;
    // Prefer touch-first devices (avoid desktop mouse clicks)
    return window.matchMedia?.('(hover: none) and (pointer: coarse)').matches ?? false;
};

const softTap = () => {
    try {
        navigator.vibrate?.(8);
    } catch {
        // no-op
    }
};

export { canUseHaptics, softTap };
