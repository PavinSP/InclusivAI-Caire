/* Caire, the animated voice guide. LOCALHOST ONLY: on any other host (e.g. GitHub Pages) this file does nothing.
   Pages call CaireGuide.show(companyId, lang, {autoplay}). The local backend (POST /guide) writes a two-sentence
   summary with Gemini, says whether the company is a good fit and points to the page for details, and voices it with
   ElevenLabs; if there is no voice clip the browser's own speech is used. */
(function(){
  if(!['localhost','127.0.0.1'].includes(location.hostname)) { window.CaireGuide = {show(){}, hide(){}}; return; }

  var css = document.createElement('style');
  css.textContent = `
  #caire-guide{position:fixed;right:20px;bottom:20px;z-index:2000;display:flex;align-items:flex-end;gap:10px;max-width:min(380px,calc(100vw - 32px));font-family:Inter,system-ui,sans-serif}
  #caire-guide[hidden]{display:none}
  #caire-guide .bubble{position:relative;background:var(--card,var(--panel,#fff));color:var(--text,var(--ink,#1e1e1e));border:1px solid var(--border,var(--line,#e6e6e6));
    border-radius:16px 16px 4px 16px;padding:12px 14px;font-size:13.5px;line-height:1.5;box-shadow:0 10px 30px -12px rgba(0,0,0,.35);animation:cg-pop .35s cubic-bezier(.22,1,.36,1) both}
  #caire-guide .bubble::after{content:'';position:absolute;right:-7px;bottom:12px;border:7px solid transparent;border-left-color:var(--border,var(--line,#e6e6e6));border-right:0}
  #caire-guide .bubble p{margin:0 0 8px}
  #caire-guide .row{display:flex;gap:8px;align-items:center}
  #caire-guide button{font:600 12px inherit;font-family:inherit;border:1px solid var(--border,var(--line,#e6e6e6));background:transparent;color:inherit;border-radius:999px;padding:5px 11px;cursor:pointer}
  #caire-guide button.play{background:#cc201e;border-color:#cc201e;color:#fff}
  #caire-guide .x{margin-left:auto;border:0;opacity:.6;padding:2px 6px}
  #caire-guide .dots span{display:inline-block;width:6px;height:6px;margin:0 2px;border-radius:50%;background:currentColor;opacity:.4;animation:cg-dot 1s infinite}
  #caire-guide .dots span:nth-child(2){animation-delay:.15s}#caire-guide .dots span:nth-child(3){animation-delay:.3s}
  #caire-guide svg{width:92px;height:auto;flex:0 0 auto;cursor:pointer;animation:cg-bob 3.2s ease-in-out infinite;filter:drop-shadow(0 6px 8px rgba(0,0,0,.25))}
  #caire-guide .eye{transform-box:fill-box;transform-origin:center;animation:cg-blink 4.5s infinite}
  #caire-guide .arm{transform-box:fill-box;transform-origin:20% 80%}
  #caire-guide.speaking .mouth{animation:cg-talk .28s ease-in-out infinite}
  #caire-guide.speaking .arm{animation:cg-wave .7s ease-in-out infinite}
  #caire-guide.speaking svg{animation-duration:1.4s}
  @keyframes cg-pop{from{opacity:0;transform:translateY(8px) scale(.96)}to{opacity:1;transform:none}}
  @keyframes cg-bob{50%{transform:translateY(-5px)}}
  @keyframes cg-blink{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
  @keyframes cg-talk{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1.1)}}
  @keyframes cg-wave{0%,100%{transform:rotate(0)}50%{transform:rotate(-24deg)}}
  @keyframes cg-dot{50%{opacity:1;transform:translateY(-3px)}}
  @media(prefers-reduced-motion:reduce){#caire-guide *{animation:none!important}}
  @media(max-width:860px){#caire-guide{bottom:64px}}`;
  document.head.appendChild(css);

  var UI = {
    en:{listen:'🔊 Listen', stop:'■ Stop', thinking:'Let me take a look', offline:'Start the local backend to hear me.', err:'I could not get a summary.'},
    de:{listen:'🔊 Anhören', stop:'■ Stopp', thinking:'Ich schaue kurz nach', offline:'Starte das lokale Backend, damit ich sprechen kann.', err:'Ich konnte keine Zusammenfassung holen.'}
  };
  var el = document.createElement('div');
  el.id = 'caire-guide'; el.hidden = true;
  el.innerHTML =
    '<div class="bubble"><p class="msg"></p><div class="row"><button class="play"></button><button class="x" aria-label="Close">✕</button></div></div>' +
    '<svg viewBox="0 0 120 150" role="img" aria-label="Caire guide">' +
      '<ellipse cx="60" cy="144" rx="30" ry="5" fill="#000" opacity=".12"/>' +
      '<rect x="30" y="92" width="60" height="46" rx="20" fill="#cc201e"/>' +
      '<rect x="52" y="100" width="16" height="30" rx="3" fill="#fff" opacity=".95"/><rect x="43" y="110" width="34" height="10" rx="3" fill="#fff" opacity=".95"/>' +
      '<g class="arm"><rect x="82" y="96" width="30" height="12" rx="6" fill="#cc201e"/><circle cx="112" cy="102" r="7" fill="#f6d2b8"/></g>' +
      '<rect x="14" y="10" width="92" height="84" rx="30" fill="#f6d2b8"/>' +
      '<path d="M14 44 Q14 8 60 8 Q106 8 106 44 Q86 24 60 24 Q36 24 14 44Z" fill="#1e1e1e"/>' +
      '<g class="eye"><ellipse cx="42" cy="56" rx="7" ry="8" fill="#fff"/><circle cx="43" cy="57" r="4" fill="#1e1e1e"/></g>' +
      '<g class="eye"><ellipse cx="78" cy="56" rx="7" ry="8" fill="#fff"/><circle cx="79" cy="57" r="4" fill="#1e1e1e"/></g>' +
      '<circle cx="31" cy="70" r="6" fill="#ff8a7a" opacity=".5"/><circle cx="89" cy="70" r="6" fill="#ff8a7a" opacity=".5"/>' +
      '<g class="mouthbox" style="transform-box:fill-box"><ellipse class="mouth" cx="60" cy="76" rx="9" ry="6" fill="#8c1a18" style="transform-box:fill-box;transform-origin:center"/></g>' +
    '</svg>';
  document.addEventListener('DOMContentLoaded', function(){ document.body.appendChild(el); });

  var msg, playBtn, audio = null, token = 0, lastArgs = null, speech = null;
  function q(s){ return el.querySelector(s); }
  function lang(){ return lastArgs && lastArgs.lang === 'de' ? 'de' : 'en'; }
  function setSpeaking(on){ el.classList.toggle('speaking', on); if(playBtn) playBtn.textContent = on ? UI[lang()].stop : UI[lang()].listen; }
  function stop(){
    if(audio){ audio.pause(); audio = null; }
    if(window.speechSynthesis) speechSynthesis.cancel();
    setSpeaking(false);
  }
  function speak(data){
    stop();
    if(data.audio){
      audio = new Audio(data.audio);
      audio.onended = audio.onpause = function(){ setSpeaking(false); };
      audio.onplay = function(){ setSpeaking(true); };
      return audio.play();
    }
    if(window.speechSynthesis){
      var u = new SpeechSynthesisUtterance(data.text);
      u.lang = lang()==='de' ? 'de-DE' : 'en-GB'; u.rate = .92;
      u.onstart = function(){ setSpeaking(true); }; u.onend = u.onerror = function(){ setSpeaking(false); };
      speechSynthesis.speak(u);
    }
    return Promise.resolve();
  }
  function init(){
    msg = q('.msg'); playBtn = q('.play');
    q('.x').onclick = function(){ stop(); el.hidden = true; };
    q('svg').onclick = function(){ if(el.hidden) return; q('.bubble').style.display = q('.bubble').style.display === 'none' ? '' : 'none'; };
    playBtn.onclick = function(){ if(el.classList.contains('speaking')) stop(); else if(el._data) speak(el._data); };
  }
  function ready(fn){ if(document.body) fn(); else document.addEventListener('DOMContentLoaded', fn); }

  window.CaireGuide = {
    hide: function(){ ready(function(){ stop(); el.hidden = true; }); },
    show: function(id, language, opts){
      ready(function(){
        if(!msg) init();
        var my = ++token; lastArgs = {id:id, lang:language}; stop();
        el.hidden = false; q('.bubble').style.display = '';
        msg.innerHTML = UI[lang()].thinking + ' <span class="dots"><span></span><span></span><span></span></span>';
        playBtn.hidden = true; el._data = null;
        fetch('/guide', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id:id, lang:language})})
          .then(function(r){ return r.json().then(function(j){ if(!r.ok) throw new Error(j.error||r.status); return j; }); })
          .then(function(data){
            if(my !== token) return;
            msg.textContent = data.text; el._data = data; playBtn.hidden = false; playBtn.textContent = UI[lang()].listen;
            if(opts && opts.autoplay) speak(data).catch(function(){ /* autoplay blocked: the Listen button is there */ });
          })
          .catch(function(){ if(my === token){ msg.textContent = UI[lang()].err; } });
      });
    }
  };
})();
