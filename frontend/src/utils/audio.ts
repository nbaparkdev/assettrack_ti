export const playNotificationSound = () => {
  try {
    const audio = new Audio('/notificacao_alerta.mp3');
    audio.volume = 0.9;
    void audio.play().catch(() => {
      // Browsers may block autoplay until the monitor receives a user interaction.
    });
  } catch (e) {
    console.warn('[NOTIFICATION_SOUND] Failed to play notification sound:', e);
  }
};

export const playEmergencyAlarm = playNotificationSound;
