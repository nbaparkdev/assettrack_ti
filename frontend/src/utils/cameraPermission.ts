import { Capacitor, registerPlugin } from '@capacitor/core';

type CameraPermissionResult = { camera: 'granted' | 'denied' | 'prompt' };

interface CameraPermissionsPlugin {
  checkPermissions(): Promise<CameraPermissionResult>;
  requestPermissions(): Promise<CameraPermissionResult>;
}

const CameraPermissions = registerPlugin<CameraPermissionsPlugin>('CameraPermissions');

/**
 * Requests the Android OS permission before Html5Qrcode opens the WebView
 * video stream. Browsers retain their normal getUserMedia permission flow.
 */
export const ensureCameraPermission = async (): Promise<boolean> => {
  if (!Capacitor.isNativePlatform() || Capacitor.getPlatform() !== 'android') return true;

  try {
    const current = await CameraPermissions.checkPermissions();
    if (current.camera === 'granted') return true;

    const requested = await CameraPermissions.requestPermissions();
    return requested.camera === 'granted';
  } catch (error) {
    console.warn('[CAMERA_PERMISSION] Native camera permission could not be verified:', error);
    return false;
  }
};

export const cameraPermissionMessage =
  'Permita o acesso à câmera para ler o QR Code. Se a permissão foi negada, ative Câmera nas configurações do aplicativo.';
