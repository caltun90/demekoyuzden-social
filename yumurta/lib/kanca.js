// Kanca yazısı: ilk karede dev, okunaklı, en fazla 5 kelimelik yazı (kanal kuralı: ilk 2 saniye kancası).
// Kullanım (story.js):
//   import { kancaYazisi } from '/lib/kanca.js';
//   export function overlay(g, t, ctx) { kancaYazisi(g, t, ctx.W, ctx.H, 'DUŞTA NEDEN FİKİR GELİR?'); }
// Yazı 0:00'da tam görünür (ilk kare kapak olur), 2,0-2,4 sn arasında söner. Altyazıyla çakışmaz.
// KAPAK GÜVENLİ ALANI (Cem, 24 Kasım 2026): Instagram ve TikTok profil ızgarası dikey kapağın yalnızca ortadaki 3:4
// bölümünü gösterir (üstten ve alttan yüzde 12,5 kesilir). Bu yüzden dikeyde yazı yüzde 20'den başlar (iki satır
// yaklaşık yüzde 17-29 arasını kaplar); yüzde 13'te duran eski yazının üst satırı ızgarada kesiliyordu. `y` değerini
// 0,18'in altına indirme. İlk karede yüzler ve ana nesne yüzde 30-80 arasında kalsın. Yatayda yüzde 12.
export function kancaYazisi(g, t, W, H, text, { until = 2.0, fade = .4, y, size, color = '#ffe15a' } = {}) {
  if (t > until + fade) return;
  const land = W > H, a = t < until ? 1 : 1 - (t - until) / fade;
  const words = text.trim().split(/\s+/);
  const lines = words.length <= 2 ? [words.join(' ')] : [words.slice(0, Math.ceil(words.length / 2)).join(' '), words.slice(Math.ceil(words.length / 2)).join(' ')];
  const s = (size || (land ? 92 : 104)) * Math.min(W, H) / 1080;
  const pop = t < .12 ? 1 + (1 - t / .12) * .08 : 1, y0 = (y ?? (land ? .12 : .2)) * H;
  g.save(); g.globalAlpha = a; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
  g.font = `900 ${s * pop}px "Segoe UI Black", "Arial Black", sans-serif`;
  lines.forEach((ln, i) => {
    const yy = y0 + i * s * 1.12;
    g.shadowColor = 'rgba(10,6,20,.55)'; g.shadowBlur = s * .2; g.shadowOffsetY = s * .07;
    g.strokeStyle = '#140c1c'; g.lineWidth = s * .22; g.strokeText(ln, W / 2, yy);
    g.shadowColor = 'transparent'; g.fillStyle = i === lines.length - 1 ? color : '#ffffff'; g.fillText(ln, W / 2, yy);
  });
  g.restore();
}
