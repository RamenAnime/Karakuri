// 80 mm drive wheel for a 4 mm D shaft (JGA25-370 output).
// Groove around the rim takes two 3 mm O-rings or a printed TPU tire.
// M3 grub screw bears on the shaft flat. Print 2, flat face down.

include <common.scad>

wheel_d = 80;
wheel_w = 12;
shaft_d = 4.2;
shaft_flat = 3.7;   // distance across the D flat
hub_d = 16;
hub_len = 10;

module wheel() {
    difference() {
        union() {
            cylinder(d = wheel_d, h = wheel_w);
            cylinder(d = hub_d, h = wheel_w + hub_len);
        }
        // D shaft bore
        translate([0, 0, -0.5])
            linear_extrude(wheel_w + hub_len + 1)
                intersection() {
                    circle(d = shaft_d);
                    translate([-(shaft_d - shaft_flat) - shaft_d / 2 + shaft_d, 0])
                        square([shaft_d, shaft_d + 1], center = true);
                }
        // Grub screw
        translate([0, 0, wheel_w + hub_len / 2])
            rotate([0, 90, 0]) cylinder(d = 2.6, h = hub_d);
        // Tire grooves
        for (z = [3.5, 8.5])
            translate([0, 0, z])
                rotate_extrude()
                    translate([wheel_d / 2, 0]) circle(d = 3.4);
        // Spoke windows
        for (a = [0:60:300])
            rotate([0, 0, a])
                translate([wheel_d / 4 + 4, 0, 0]) hole(16, wheel_w);
    }
}

wheel();
