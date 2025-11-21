# Kyrix Client

Kyrix Client, SonoyuncuClient (oyun istemcisi) için geliştirilmiş bir yardımcı uygulamadır.  
Amaç: Throwpot (slot değiştirip sağ tık) ve Sol Click otomasyonlarını kolayca yönetmek.  
Not: Uygulama yalnızca SonoyuncuClient pencere/işlemine ön planda iken tetikleme yapar — başka pencerelerde çalışmaz.

## Önemli Uyarılar
- Oyun içi otomasyon bazı oyunlarda kurallara/anti-cheat'e aykırı olabilir. Bu yazılımı kullanmak tamamen kendi sorumluluğunuzdadır.
- Uygulamayı çalıştırırken sistemdeki güvenlik yazılımları (AV) uyarı verebilir.
- Eğer oyun ya da başka bir uygulama yönetici (admin) yetkisiyle çalışıyorsa, Kyrix Client'i de yönetici olarak çalıştırmanız gerekebilir (aşağıda nasıl exe üreteceğinizde bunu anlatıyorum).

## Gereksinimler (Python)
Aşağıdaki paketler gerekli:
- Python (3.8+ tavsiye)
- pynput
- pyautogui
- psutil
- keyboard
- pywin32

Kurulum (CMD / PowerShell):
- pip zaten çalışıyorsa:
  ```
  py -m pip install --user pynput pyautogui psutil keyboard pywin32
  ```
- Ayrıca `.exe` üretmek için (isteğe bağlı):
  ```
  py -m pip install --user pyinstaller
  ```

(Not: pyautogui bazı sistemlerde ek paket gerektirebilir; hata alırsanız pip çıktısına bakıp eksik paketleri kurun.)

## Hızlı Başlangıç (Geliştirici / Test)
- Dosya aynı klasördeyken çalıştır:
  ```
  py kyrix_client.py
  ```
- Uygulama açılacaktır. UI üzerinden "Throwpot Ekle" veya "+ Sol Click Ekle" ile kart ekleyip konfigüre edebilirsin.

## Nasıl Çalışır / Kullanım Özeti
- Throwpot Kartı:
  - Delay: 100 - 500 ms aralığında ayarlanır (slot'a geçip hemen sağ tıklama, sonra olta/bekleme, sonra return slot).
  - Return Slot: geri dönülecek slot (1-9).
  - Click Slot: sağ tıkın atılacağı slot (1-9).
  - Tuş Atama: tuş atama moduna gir, klavyeden veya mouse yan tuşlarından (MBUTTON1/X1, MBUTTON2/X2, MBUTTON3/middle) seç. ESC ile atama iptal edilir ve mevcut atama temizlenir.
  - Kart başına execution lock / suppress mekanizması vardır: aynı anda bir kartın re-entry yapması veya simüle edilen tuşların yeniden tetikleme yaratması engellenmiştir.

- Sol Click Kartı:
  - Delay (ms): 1 - 20 ms arası (kullanıcı ayarı). Not: gerçekçi ve güvenilir aralık işletim sistemi ve pyautogui overhead'i nedeniyle ~8-16ms aralığı önerilir.
  - Click Slot: birden çok slot seçilebilir; seçili slotlarda bulunduğun ve fiziksel sol tuşa bastığın sürece sol click tekrarlı atılır.
  - Sol click sadece fiziksel sol tuşa basılı tutulduğunda tetiklenir (otomatik olarak tetiklenmez).
  - Sol click, uygulamanın ürettiği sentetik mouse eventlerinin listener tarafından fiziksel bırakma gibi algılanmaması için bir ignore dönemi kullanır — bu sayede kullanıcı basılı tuttuğu sürece tıklama devam eder.

- Genel:
  - Uygulama yalnızca SonoyuncuClient ön planda iken tetikleme yapar. (Process adı `sonoyuncuclient.exe` kontrolü yapılır; farklı bir exe adı kullanıyorsa kodu güncelleyin.)
  - Maksimum kart sayısı: UI limiti ile belirlenmiştir (ör. 5).
  - ESC: atama modunda ESC ile atama iptal edilir ve varsa eski atama temizlenir.
  - MBUTTON4 desteği çoğu sistemde garanti değildir; ekstra yan tuşlar için alternatif input paketleri gerekebilir.

## .exe Üretme (PyInstaller)
- Basit tek-file ve ikonlu build (UAC / yönetici istemi ile):
  ```
  py -m PyInstaller --onefile --noconsole --icon=app.ico --name KyrixClient --uac-admin kyrix_client.py
  ```
  - `--uac-admin` parametresi exe çalıştırıldığında UAC istemi açar ve uygulamayı yönetici yetkisi ile başlatır. Eğer oyunu da admin olarak çalıştırıyorsanız bu gereklidir.
  - Eğer build sonrası exe hemen kapanıyorsa debug için önce konsollu build yapıp hata çıktısını inceleyin:
  ```
  py -m PyInstaller --onedir --console --name KyrixClient kyrix_client.py
  ```

- Eğer PyInstaller hata verirse:
  - Hata mesajındaki eksik modül isimlerini pip ile kurun.
  - PyInstaller'ın otomatik algılamadığı modülleri `--hidden-import` ile ekleyin:
  ```
  py -m PyInstaller --onefile --console --hidden-import=pynput.keyboard --hidden-import=pynput.mouse --icon=app.ico kyrix_client.py
  ```

## Ayarlar ve Özelleştirme
- `in_game()` kontrolü: `sonoyuncuclient.exe` olarak kontrol eder. Farklı bir process adı/pencere başlığı gerekiyorsa bu fonksiyonu ilgili exe veya başlığa göre düzenleyin.
- Delay değerleri:
  - Throwpot: 100–500 ms (UI slider olarak ayarlanır)
  - Sol Click: 1–20 ms (pratikte çok düşük değerlerde OS/timing overhead sınırlı olabilir)
- pyautogui güvenlik: kodda `pyautogui.FAILSAFE = False` kullanılmış olabilir. Geliştirme sırasında `True` yapman, fareyi ekran köşesine götürerek otomatik durdurma (failsafe) sağlar.

## Sorun Giderme (Troubleshooting)
- Keybind yakalanmıyor / mouse yan tuşları çalışmıyor:
  - Uygulamayı Yönetici olarak çalıştırmayı dene (özellikle oyun elevated ise).
  - `pynput` ve `keyboard` paketlerinin kurulu olduğundan emin ol.
- Executable derlendi ama çalışmıyor / çabuk kapanıyor:
  - Konsollu build yap ve exe'yi CMD'den çalıştır; trace/backtrace'i oku.
- Sol click birkaç kez atıp duruyor:
  - Listener'in sentetik mouse eventleri algılamasını engelleyen ignore sürelerini ayarlayın; left-click kartındaki delay / ignore parametresini artırın.
- MBUTTON4 gerekliyse:
  - Platforma / mouse modeline göre `pynput` x1/x2/middle dışında destek vermeyebilir; ek tuşlar için `mouse` paketi veya raw input (win32) gerekir.

## Güvenlik ve Etik
- Otomasyon kullanımı oyunun kurallarına/servis şartlarına aykırı olabilir. Bu yazılımı kullanmadan önce sunucu kurallarını ve geliştiricilerin kullanım şartlarını kontrol edin.
- Yüksek izinlerle çalışma (UAC) isteniyorsa kullanıcıyı bilgilendirin.

## Lisans & Atıf
- Proje açık kaynak olarak paylaşılacaksa lisans seçimini burada belirtin (ör. MIT, GPL). Varsayılan olarak bir lisans eklenmedi — dağıtmadan önce uygun lisansı ekleyin.
