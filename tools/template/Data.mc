import Toybox.Activity;
import Toybox.ActivityMonitor;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.Time.Gregorian;
import Toybox.Weather;

// Werte fuer die Elemente aus dem Design-Editor (gleiche Typnamen wie im JSON)
module Data {

    function hours() as String {
        var hour = System.getClockTime().hour;
        if (!System.getDeviceSettings().is24Hour) {
            hour = hour % 12;
            if (hour == 0) {
                hour = 12;
            }
        }
        return hour.format("%02d");
    }

    function minutes() as String {
        return System.getClockTime().min.format("%02d");
    }

    function seconds() as String {
        return System.getClockTime().sec.format("%02d");
    }

    function time() as String {
        return hours() + ":" + minutes();
    }

    function ampm() as String {
        return System.getClockTime().hour < 12 ? "AM" : "PM";
    }

    function info() as Gregorian.Info {
        return Gregorian.info(Time.now(), Time.FORMAT_MEDIUM);
    }

    function weekday() as String {
        return (info().day_of_week as String).toUpper();
    }

    function day() as String {
        return info().day.toString();
    }

    function month() as String {
        return (info().month as String).toUpper();
    }

    function year() as String {
        return info().year.toString();
    }

    function date() as String {
        var i = Gregorian.info(Time.now(), Time.FORMAT_SHORT);
        var weekdays = ["So.", "Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa."];
        return weekdays[(i.day_of_week as Number) - 1] + " " + i.day.format("%02d") + "." + (i.month as Number).format("%02d") + ".";
    }

    function battery() as String {
        return System.getSystemStats().battery.toNumber() + "%";
    }

    function temperature() as String {
        var conditions = Weather.getCurrentConditions();
        if (conditions == null || conditions.temperature == null) {
            return "--";
        }
        var t = conditions.temperature as Numeric;
        if (System.getDeviceSettings().temperatureUnits == System.UNIT_STATUTE) {
            t = t * 9.0 / 5.0 + 32;
        }
        return t.toNumber() + "°";
    }

    function distance() as String {
        var cm = ActivityMonitor.getInfo().distance;
        if (cm == null) {
            return "--";
        }
        var metric = System.getDeviceSettings().distanceUnits == System.UNIT_METRIC;
        return (metric ? cm / 100000.0 : cm / 160934.4).format("%.1f");
    }

    function number(value as Number?) as String {
        return value == null ? "--" : value.toString();
    }

    function steps() as String {
        return number(ActivityMonitor.getInfo().steps);
    }

    function calories() as String {
        return number(ActivityMonitor.getInfo().calories);
    }

    function floors() as String {
        return number(ActivityMonitor.getInfo().floorsClimbed);
    }

    function activeMinutes() as String {
        var active = ActivityMonitor.getInfo().activeMinutesDay;
        return active == null ? "--" : number(active.total);
    }

    function heartRate() as String {
        var activity = Activity.getActivityInfo();
        var hr = activity != null ? activity.currentHeartRate : null;
        if (hr == null) {
            var sample = ActivityMonitor.getHeartRateHistory(1, true).next();
            if (sample != null && sample.heartRate != ActivityMonitor.INVALID_HR_SAMPLE) {
                hr = sample.heartRate;
            }
        }
        return number(hr);
    }

    function notifications() as String {
        return System.getDeviceSettings().notificationCount.toString();
    }

    function alarmCount() as String {
        return System.getDeviceSettings().alarmCount.toString();
    }
}
