import { Capacitor } from '@capacitor/core';
import { LocalNotifications } from '@capacitor/local-notifications';

const CHANNEL_ID = 'assettrack-alertas';
const SOUND_FILE = 'notificacao_alerta.mp3';
let initialized = false;

export const isAndroidApp = () => Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android';

export const initializeAndroidNotifications = async () => {
  if (!isAndroidApp() || initialized) return;
  initialized = true;

  try {
    await LocalNotifications.createChannel({
      id: CHANNEL_ID,
      name: 'Alertas do AssetTrack TI',
      description: 'Alertas emergenciais e novidades operacionais do AssetTrack TI',
      importance: 5,
      visibility: 1,
      vibration: true,
      lights: true,
      lightColor: '#ef4444',
      sound: SOUND_FILE,
    });

    const permissions = await LocalNotifications.checkPermissions();
    if (permissions.display !== 'granted') {
      await LocalNotifications.requestPermissions();
    }
  } catch (error) {
    initialized = false;
    console.warn('[ANDROID_NOTIFICATIONS] Permission/channel setup failed:', error);
  }
};

export const notifyAndroid = async (title: string, body: string, extra?: Record<string, unknown>) => {
  if (!isAndroidApp()) return;
  try {
    const permissions = await LocalNotifications.checkPermissions();
    if (permissions.display !== 'granted') return;
    await LocalNotifications.schedule({
      notifications: [{
        id: Math.floor(Date.now() % 2147483647),
        title,
        body,
        channelId: CHANNEL_ID,
        sound: SOUND_FILE,
        smallIcon: 'ic_launcher',
        extra,
      }],
    });
  } catch (error) {
    console.warn('[ANDROID_NOTIFICATIONS] Notification failed:', error);
  }
};
