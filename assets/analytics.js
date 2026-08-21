/* 
  Optional GA4 loader. Set window.SEPHIRIA_GA_ID = "G-XXXXXXXX" before this
  script, or edit GA_ID below once Jerome creates the property.
*/
(function () {
  var GA_ID = window.SEPHIRIA_GA_ID || "G-X8S6QVZB0E";
  if (!GA_ID || GA_ID.indexOf("G-") !== 0) return;
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag("js", new Date());
  gtag("config", GA_ID);
})();
