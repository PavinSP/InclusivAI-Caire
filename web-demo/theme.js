/* Light/dark theme for every Caire page. Follows the system until the visitor picks one; the choice is
   remembered per browser. Pages style themselves from html[data-theme]; the map listens for 'themechange'. */
(function(){
  var KEY = 'caire-theme', root = document.documentElement;
  function stored(){ try{ return localStorage.getItem(KEY); }catch(e){ return null; } }
  function system(){ return window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; }
  function current(){ var s = stored(); return s==='dark' || s==='light' ? s : system(); }
  function apply(t){
    root.setAttribute('data-theme', t);
    document.querySelectorAll('.theme-toggle').forEach(function(b){
      b.textContent = t==='dark' ? '☀' : '☾';
      b.setAttribute('aria-label', t==='dark' ? 'Switch to light mode' : 'Switch to dark mode');
    });
    document.dispatchEvent(new CustomEvent('themechange', {detail:t}));
  }
  apply(current());
  var css = document.createElement('style');
  css.textContent =
    'html[data-theme="dark"] img[src="logo.png"]{filter:invert(1) hue-rotate(180deg)}' +
    '.theme-toggle{border:1px solid currentColor;border-radius:999px;background:transparent;color:inherit;opacity:.8;' +
    'width:30px;height:30px;font-size:15px;line-height:1;cursor:pointer;flex:0 0 auto;margin-left:8px}' +
    '.theme-toggle:hover{opacity:1}';
  document.head.appendChild(css);
  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('.lang, .lang-switch').forEach(function(el){
      var b = document.createElement('button');
      b.className = 'theme-toggle'; b.type = 'button';
      b.onclick = function(){
        var t = root.getAttribute('data-theme')==='dark' ? 'light' : 'dark';
        try{ localStorage.setItem(KEY, t); }catch(e){}
        apply(t);
      };
      el.parentNode.insertBefore(b, el.nextSibling);
    });
    apply(current());
  });
  if(window.matchMedia) matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(){ if(!stored()) apply(system()); });
})();
