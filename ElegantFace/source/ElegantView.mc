import Toybox.ActivityMonitor;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.Time.Gregorian;
import Toybox.WatchUi;
import Toybox.Weather;

// Zifferblatt "Elegant" – Positionen aus mein-design.json (Design-Flaeche 448 x 486)
class ElegantView extends WatchUi.WatchFace {

    const DESIGN_W = 448;
    const DESIGN_H = 486;

    const GOLD = 0xE8CD91;
    const CREAM = 0xF2E7CF;
    const GREY = 0xD9DDE1;
    const DIM_GOLD = 0x6E6045;

    // Mittelpunkte der drei unteren Spalten (Icon-x + 45/2)
    const COL_X = [84, 226, 368];

    private var _fHours as FontResource?;
    private var _fSeconds as FontResource?;
    private var _fValue as FontResource?;
    private var _fBattery as FontResource?;
    private var _fDate as FontResource?;
    private var _fLabel as FontResource?;
    private var _icons as Array<BitmapResource> = [];

    private var _ox as Number = 0;
    private var _oy as Number = 0;
    private var _sleeping as Boolean = false;

    function initialize() {
        WatchFace.initialize();
    }

    function onLayout(dc as Dc) as Void {
        _fHours = WatchUi.loadResource(Rez.Fonts.Hours) as FontResource;
        _fSeconds = WatchUi.loadResource(Rez.Fonts.Seconds) as FontResource;
        _fValue = WatchUi.loadResource(Rez.Fonts.Value) as FontResource;
        _fBattery = WatchUi.loadResource(Rez.Fonts.Battery) as FontResource;
        _fDate = WatchUi.loadResource(Rez.Fonts.Date) as FontResource;
        _fLabel = WatchUi.loadResource(Rez.Fonts.Label) as FontResource;
        _icons = [
            WatchUi.loadResource(Rez.Drawables.IconSun) as BitmapResource,
            WatchUi.loadResource(Rez.Drawables.IconRun) as BitmapResource,
            WatchUi.loadResource(Rez.Drawables.IconAlarm) as BitmapResource
        ];
        // Design zentrieren, falls das Display etwas anders gross ist
        _ox = (dc.getWidth() - DESIGN_W) / 2;
        _oy = (dc.getHeight() - DESIGN_H) / 2;
    }

    function onUpdate(dc as Dc) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var clock = System.getClockTime();
        var settings = System.getDeviceSettings();
        var hour = clock.hour;
        if (!settings.is24Hour) {
            hour = hour % 12;
            if (hour == 0) {
                hour = 12;
            }
        }
        var hh = hour.format("%02d");
        var mm = clock.min.format("%02d");

        if (_sleeping) {
            drawAlwaysOn(dc, hh + ":" + mm, clock.min);
            return;
        }

        // Datum und Akku
        text(dc, 36, 44, _fDate, GOLD, dateString(), Graphics.TEXT_JUSTIFY_LEFT);
        var battery = System.getSystemStats().battery.toNumber();
        text(dc, 413, 36, _fBattery, CREAM, battery + "%", Graphics.TEXT_JUSTIFY_RIGHT);

        // Linien
        dc.setColor(GOLD, Graphics.COLOR_TRANSPARENT);
        dc.fillRectangle(_ox + 35, _oy + 95, 378, 1);
        dc.fillRectangle(_ox + 35, _oy + 320, 378, 1);

        // Uhrzeit
        text(dc, 28, 144, _fHours, GOLD, hh, Graphics.TEXT_JUSTIFY_LEFT);
        text(dc, 184, 144, _fHours, GOLD, mm, Graphics.TEXT_JUSTIFY_LEFT);
        text(dc, 368, 192, _fSeconds, GOLD, clock.sec.format("%02d"), Graphics.TEXT_JUSTIFY_LEFT);

        // Icons
        for (var i = 0; i < 3; i++) {
            dc.drawBitmap(_ox + COL_X[i] - 22, _oy + 333, _icons[i]);
        }

        // Werte
        var metric = settings.distanceUnits == System.UNIT_METRIC;
        var center = Graphics.TEXT_JUSTIFY_CENTER;
        text(dc, COL_X[0], 389, _fValue, GOLD, temperatureString(settings), center);
        text(dc, COL_X[1], 388, _fValue, GOLD, distanceString(metric), center);
        var alarms = settings.alarmCount;
        text(dc, COL_X[2], 389, _fValue, GOLD, alarms.toString(), center);

        // Beschriftungen
        text(dc, COL_X[0], 432, _fLabel, GREY, "WETTER", center);
        text(dc, COL_X[1], 431, _fLabel, GREY, metric ? "KM HEUTE" : "MI HEUTE", center);
        text(dc, COL_X[2], 431, _fLabel, GREY, "WECKER", center);
    }

    // Always-on (AMOLED): nur eine kleine, gedimmte Uhrzeit, die jede Minute
    // ein wenig wandert, damit das Display nicht einbrennt.
    private function drawAlwaysOn(dc as Dc, time as String, minute as Number) as Void {
        var dx = (minute % 5) * 6 - 12;
        var dy = ((minute / 5) % 5) * 6 - 12;
        dc.setColor(DIM_GOLD, Graphics.COLOR_TRANSPARENT);
        dc.drawText(dc.getWidth() / 2 + dx, dc.getHeight() / 2 - 30 + dy, _fSeconds as FontResource,
                    time, Graphics.TEXT_JUSTIFY_CENTER);
    }

    private function text(dc as Dc, x as Number, y as Number, font as FontResource?, color as Number,
                          value as String, justify as Number) as Void {
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(_ox + x, _oy + y, font as FontResource, value, justify);
    }

    private function dateString() as String {
        var info = Gregorian.info(Time.now(), Time.FORMAT_MEDIUM);
        var dow = (info.day_of_week as String).toUpper();
        var month = (info.month as String).toUpper();
        return dow + " " + info.day + ". " + month;
    }

    private function temperatureString(settings as DeviceSettings) as String {
        var conditions = Weather.getCurrentConditions();
        if (conditions == null || conditions.temperature == null) {
            return "--";
        }
        var t = conditions.temperature as Numeric;
        if (settings.temperatureUnits == System.UNIT_STATUTE) {
            t = t * 9.0 / 5.0 + 32;
        }
        return t.toNumber() + "°";
    }

    private function distanceString(metric as Boolean) as String {
        var cm = ActivityMonitor.getInfo().distance;
        if (cm == null) {
            return "--";
        }
        var dist = metric ? cm / 100000.0 : cm / 160934.4;
        return dist.format("%.1f");
    }

    function onEnterSleep() as Void {
        _sleeping = System.getDeviceSettings().requiresBurnInProtection;
        WatchUi.requestUpdate();
    }

    function onExitSleep() as Void {
        _sleeping = false;
        WatchUi.requestUpdate();
    }
}
