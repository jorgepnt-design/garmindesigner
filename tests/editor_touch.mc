import Toybox.Test;
import Toybox.Complications;

class TouchTestFace {
 var displayWidth=448;var displayHeight=486;
 function initialize() {}
}
class TouchTestEvent {
 var x;var y;
 function initialize(px,py) { x=px;y=py; }
 function getCoordinates() { return [x,y]; }
}
// Intercept only the system handoff so routing can be tested without leaving
// the test runner for a Garmin system app.
class RecordingDelegate extends CustomDelegate {
 var launchedType=null;
 function initialize(face) { CustomDelegate.initialize(face); }
 function launchComplication(type) { launchedType=type; }
}

(:test)
function stringComparisonRequiresValueEquality(logger) {
 var literal="weather";var allocated="xweather".substring(1,8);
 Test.assert(literal!=allocated);Test.assert(literal.equals(allocated));return true;
}
(:test)
function weatherSymbolValueAndLabelLaunchNativeWeather(logger) {
 var points=[[82,352],[80,404],[80,441]];
 for(var i=0;i<points.size();i+=1) {
  var delegate=new RecordingDelegate(new TouchTestFace());
  Test.assert(delegate.onPress(new TouchTestEvent(points[i][0],points[i][1])));
  Test.assert(delegate.launchedType==Complications.COMPLICATION_TYPE_CURRENT_WEATHER);
 }
 return true;
}
(:test)
function allocatedWeatherTargetLaunchesNativeWeather(logger) {
 var delegate=new RecordingDelegate(new TouchTestFace());
 Test.assert(delegate.open("xweather".substring(1,8)));
 Test.assert(delegate.launchedType==Complications.COMPLICATION_TYPE_CURRENT_WEATHER);
 return true;
}
(:test)
function clockAndAlarmCoordinatesDoNothing(logger) {
 var delegate=new RecordingDelegate(new TouchTestFace());
 Test.assert(!delegate.onPress(new TouchTestEvent(239,257)));
 Test.assert(!delegate.onPress(new TouchTestEvent(380,441)));
 Test.assert(delegate.launchedType==null);return true;
}
(:test)
function stepsBatteryAndDateStillLaunchTheirSystemViews(logger) {
 var delegate=new RecordingDelegate(new TouchTestFace());
 var points=[[230,404],[370,70],[100,75]];
 var types=[Complications.COMPLICATION_TYPE_STEPS,Complications.COMPLICATION_TYPE_BATTERY,Complications.COMPLICATION_TYPE_DATE];
 for(var i=0;i<points.size();i+=1) {
  Test.assert(delegate.onPress(new TouchTestEvent(points[i][0],points[i][1])));
  Test.assert(delegate.launchedType==types[i]);
 }
 return true;
}
