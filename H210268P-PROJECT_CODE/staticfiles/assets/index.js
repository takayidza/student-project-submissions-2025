// Code to handle install prompt on desktop
let deferredPrompt;
const pwaBtn = document.querySelector('.pwa-btn');
const installText = document.querySelector('.pwa-text');

/* for ios start */
function isThisDeviceRunningiOS(){
  if (['iPad Simulator', 'iPhone Simulator','iPod Simulator', 'iPad','iPhone','iPod','ios'].includes(navigator.platform) || navigator.userAgent.indexOf('Mac OS X') != -1){ 
	installText.innerHTML = 'Install Jobie job portal mobile app template to your home screen for easy access click to safari share option "Add to Home Screen".';
	pwaBtn.remove();
	return true;
  } 
}
isThisDeviceRunningiOS();	
/* for ios start */

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;

  pwaBtn.addEventListener('click', () => {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the A2HS prompt');
      } else {
        console.log('User dismissed the A2HS prompt');
      }
      deferredPrompt = null;
    });
  });
});

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('error.html').then((cache) => cache.addAll([
      '/mobile-app/xhtml/'
    ])),
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then(function (response) {
      return response || fetch(e.request);
    })
  );
});