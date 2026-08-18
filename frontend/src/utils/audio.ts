export const playEmergencyAlarm = () => {
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) return;
    
    const ctx = new AudioContextClass();
    const now = ctx.currentTime;
    
    // Play 3 loud alarm beeps in sequence
    const beepTimes = [0, 0.25, 0.5, 0.75];
    
    beepTimes.forEach((offset) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(950, now + offset); // high pitch warning tone
      osc.frequency.exponentialRampToValueAtTime(450, now + offset + 0.18);
      
      gain.gain.setValueAtTime(0.4, now + offset);
      gain.gain.exponentialRampToValueAtTime(0.01, now + offset + 0.18);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start(now + offset);
      osc.stop(now + offset + 0.2);
    });
  } catch (e) {
    console.warn('[EMERGENCY_SOUND] Failed to synthesize Web Audio alarm tone:', e);
  }
};
