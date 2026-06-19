// Sweeper attachment. A counter-rotating brush roller (a cheap 25 mm
// replacement vacuum brush, cut to 140 mm) driven by an N20 gear motor
// flicks debris up a ramp into a snap-out bin. A micro servo at each
// end lowers the whole cradle so the same robot vacuums with this
// raised and sweeps with it down. Bolts to the deck intake four_holes
// pattern (56 x 56 M3). Print cradle, bin, and two end caps; cradle
// and bin flat, caps flat, no supports.
include <common.scad>

roller_d = 26; span = 150; wall = 3;

module sweeper_cradle() {
    difference() {
        union() {
            // back wall and ramp into the bin
            translate([0, 18, 0]) cube([span, wall, 44], center = false ? false : true);
            // two side walls
            for (s = [-1, 1]) translate([s * (span/2 - wall/2), 0, 0])
                cube([wall, 60, 40], center = true);
            // deck flange on top
            translate([0, 0, 36]) rounded_plate(70, 70, 5, 6);
        }
        four_holes(56, 56, m3, 5);                        // matches deck intake
        // roller bearing pockets in the side walls
        for (s = [-1, 1]) translate([s * span/2, -10, 12])
            rotate([0, 90, 0]) translate([0,0,-wall-1]) cylinder(d = 4.2, h = wall + 2);
        // N20 motor saddle in one wall
        translate([span/2 - wall, -10, 12]) rotate([0, 90, 0]) translate([0,0,-wall-1]) cylinder(d = 12.2, h = wall*3);
    }
}
module brush_bin() {                                       // snaps onto the cradle back
    difference() {
        cube([span - 8, 46, 40], center = true);
        translate([0, 0, 4]) cube([span - 8 - 2*wall, 46 - 2*wall, 40], center = true);
        // finger notch
        translate([0, 23, 12]) rotate([90,0,0]) cylinder(d = 24, h = 8);
    }
}
module sweeper_endcap() {                                  // holds the roller axle + brush
    difference() {
        cylinder(d = roller_d + 8, h = 6);
        cylinder(d = 4.2, h = 6);
        for (a = [0, 120, 240]) rotate([0,0,a]) translate([roller_d/2 - 3, 0, 0]) hole(2.2, 6);
    }
}
sweeper_cradle();
translate([0, 90, 0]) brush_bin();
translate([span/2 + 30, 0, 0]) sweeper_endcap();
