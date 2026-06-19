// Foot with retractable wheels. The sole is a wide stable plate with a
// 50 mm M4 square for the ankle joint. A swing frame carrying two N20
// gear motors with 34 mm wheels pivots in the heel bay: an MG90S in the
// arch pushes the frame down 12 degrees past centre to deploy, lifting
// the sole 6 mm so the robot skates on four wheels (two per foot, rear
// pair driven). Retracted, the wheels hide in the bay and the rubber
// sole walks. Three pieces per foot, print 2 feet. Flat, no supports.
include <servo_common.scad>

module foot_sole() {
    difference() {
        union() {
            rounded_plate(150, 95, 10, 14);
            // ankle tower
            translate([20, 0, 10]) linear_extrude(8) square([70, 70], center = true);
            // swing pivot bosses in the heel bay
            for (s = [-1, 1]) translate([-48, s * 34, 10]) cube([26, 8, 18]);
        }
        translate([20, 0, 0]) four_holes(50, 50, m4, 18);
        // wheel bay through the heel
        translate([-44, 0, 0]) translate([0,0,-0.5]) linear_extrude(11) square([54, 56], center = true);
        // pivot bolt
        for (s = [-1, 1]) translate([-48, s * 40, 22]) rotate([90, 0, 0]) cylinder(d = m4, h = 14);
        // MG90S deploy servo pocket in the arch, lever reaches the swing
        translate([-8, 0, 10]) {
            translate([0,0,-10+8]) linear_extrude(11) square([23.4, 12.8], center = true);
            for (x = [-14, 14]) translate([x, 0, 0]) hole(2.2, 18);
        }
        // sole grip grooves
        for (x = [25, 45, 65]) translate([x, 0, 0]) translate([0,0,-0.5]) slot(3, 70, 3);
    }
}
module wheel_swing() {        // U frame: pivot ears, two N20 saddles
    difference() {
        union() {
            cube([50, 64, 6]);
            for (s = [0, 58]) translate([0, s, 6]) cube([50, 6, 14]);
            translate([0, 26, 6]) cube([10, 12, 10]);   // servo link tab
        }
        // pivot holes through the ears
        for (s = [3, 61]) translate([6, s, 14]) rotate([90, 0, 0]) translate([0,0,-4]) cylinder(d = m4, h = 12);
        // N20 motor saddles (12 x 10 body) through the deck
        for (y = [8, 44]) translate([28, y, -0.5]) linear_extrude(7) square([14, 11]);
        for (y = [8, 44]) for (x = [26, 44]) translate([x, y + 5.5, 3]) rotate([0, 90, 0]) translate([0,0,-2]) cylinder(d = 2.2, h = 6);
        translate([5, 32, 6]) translate([0,0,-6.5]) cylinder(d = 2.4, h = 24);   // servo link wire hole
    }
}
foot_sole(); translate([-25, 55, 0]) wheel_swing();
