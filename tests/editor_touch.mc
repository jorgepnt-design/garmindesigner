import Toybox.Test;
import Toybox.Graphics;
import Toybox.Time;

class TouchTestFace {
 var weatherPanel=false;var displayWidth=448;var displayHeight=486;var touchPoint="";var noticeText="";
 function initialize() {}
 function showWeather() { weatherPanel=true; }
 function showNotice(value) { noticeText=value; }
 function closeWeather() { weatherPanel=false; }
}
class TouchTestEvent {
 var x;var y;
 function initialize(px,py) { x=px;y=py; }
 function getCoordinates() { return [x,y]; }
}
class WeatherTestDc {
 var texts=[];var boxes=[];var bitmap;
 function initialize() { bitmap=Graphics.createBufferedBitmap({:width=>448,:height=>486}); }
 function getWidth() { return 448; }
 function getHeight() { return 486; }
 function setColor(fg,bg) {}
 function clear() {}
 function drawLine(x1,y1,x2,y2) {}
 function fillRectangle(x,y,w,h) {}
 function drawBitmap(x,y,image) {}
 function drawText(x,y,font,text,justify) {
  texts.add(text);
  var width=bitmap.get().getDc().getTextWidthInPixels(text,font);var height=Graphics.getFontHeight(font);
  var left=x;if(justify==Graphics.TEXT_JUSTIFY_CENTER) { left=x-width/2; }
  else if(justify==Graphics.TEXT_JUSTIFY_RIGHT) { left=x-width; }
  boxes.add([left,y,left+width,y+height]);
 }
 function fitsWithoutOverlap(logger) {
  for(var i=0;i<boxes.size();i+=1) {
   var a=boxes[i];
   if(a[0]<12 || a[1]<8 || a[2]>436 || a[3]>478) { logger.debug("Out of bounds: "+texts[i]);return false; }
   for(var j=0;j<i;j+=1) {
    var b=boxes[j];
    if(a[0]<b[2] && a[2]>b[0] && a[1]<b[3] && a[3]>b[1]) { logger.debug("Overlap: "+texts[i]+" / "+texts[j]);return false; }
   }
  }
  return true;
 }
 function contains(text) {
  for(var i=0;i<texts.size();i+=1) { if(texts[i].equals(text)) { return true; } }
  return false;
 }
}
class WeatherLayoutConditions {
 var temperature=15.0;var feelsLikeTemperature=15.0;var lowTemperature=8.0;var highTemperature=14.0;
 var relativeHumidity=63.0;var windSpeed=8.88889;var observationTime;
 function initialize() { observationTime=Time.now(); }
}
class WeatherLayoutFace extends CustomFace {
 var conditions;
 function initialize() { CustomFace.initialize();conditions=new WeatherLayoutConditions(); }
 function currentWeather() { return conditions; }
}

(:test)
function stringComparisonRequiresValueEquality(logger) {
 var literal="weather";var allocated="xweather".substring(1,8);
 Test.assert(literal!=allocated);
 Test.assert(literal.equals(allocated));
 return true;
}
(:test)
function weatherSymbolValueAndLabelOpenWeather(logger) {
 var points=[[82,352],[80,404],[80,441]];
 for(var i=0;i<points.size();i+=1) {
  var face=new TouchTestFace();var delegate=new CustomDelegate(face);
  Test.assert(delegate.onPress(new TouchTestEvent(points[i][0],points[i][1])));
  Test.assert(face.weatherPanel);
 }
 return true;
}
(:test)
function allocatedWeatherTargetOpensWeather(logger) {
 var face=new TouchTestFace();var delegate=new CustomDelegate(face);
 Test.assert(delegate.open("xweather".substring(1,8)));
 Test.assert(face.weatherPanel);
 return true;
}
(:test)
function clockCoordinatesRemainUnlinked(logger) {
 var face=new TouchTestFace();var delegate=new CustomDelegate(face);
 Test.assert(delegate.onPress(new TouchTestEvent(239,257)));
 Test.assert(!face.weatherPanel);
 Test.assert(face.noticeText.find("Frei 239/257")!=null);
 return true;
}
(:test)
function alarmsShowMenuGuidance(logger) {
 var face=new TouchTestFace();var delegate=new CustomDelegate(face);
 Test.assert(delegate.onPress(new TouchTestEvent(380,441)));
 Test.assert(face.noticeText.equals("Alarme im Garmin-Uhrenmenue einstellen"));
 return true;
}
(:test)
function realWeatherViewSurvivesSleepAndRenders(logger) {
 var face=new CustomFace();
 face.onEnterSleep();face.showWeather();face.onEnterSleep();
 Test.assert(face.weatherPanel);
 face.onExitSleep();
 var dc=new WeatherTestDc();face.onUpdate(dc);
 Test.assert(face.weatherPanel);
 Test.assert(dc.contains("WETTER"));
 Test.assert(dc.contains("Oben halten: zurueck"));
 Test.assert(!face.noticeText.equals("P8: Wetterfehler"));
 face.closeWeather();
 Test.assert(!face.weatherPanel);
 return true;
}

(:test)
function weatherTextFitsWithRealVenuFonts(logger) {
 var face=new WeatherLayoutFace();face.showWeather();
 var dc=new WeatherTestDc();face.onUpdate(dc);
 Test.assert(dc.contains("15°C"));Test.assert(dc.contains("32 km/h"));
 Test.assert(dc.fitsWithoutOverlap(logger));
 Test.assert(face.noticeText.length()==0);
 // Also exercise long negative temperatures and three-digit wind speeds.
 face.conditions.temperature=-25.0;face.conditions.feelsLikeTemperature=-30.0;
 face.conditions.lowTemperature=-35.0;face.conditions.highTemperature=-12.0;
 face.conditions.windSpeed=30.0;face.conditions.relativeHumidity=100.0;
 dc=new WeatherTestDc();face.onUpdate(dc);
 Test.assert(dc.contains("-25°C"));Test.assert(dc.contains("108 km/h"));
 Test.assert(dc.fitsWithoutOverlap(logger));
 return true;
}
