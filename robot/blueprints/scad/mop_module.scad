// Mop attachment. A flat plate holds a microfiber pad (hook side up,
// cut from any flat mop refill) and a small reservoir dribbles water
// onto the floor ahead of it through three holes fed by a 5 V pump.
// Bolts to the same deck intake pattern as the vacuum and sweeper, so
// the three floor tools are interchangeable. Print plate and tank;
// plate flat, tank with the open side up, no supports.
include <common.scad>

plate_w = 150; plate_d = 90;

module mop_plate() {
    difference() {
        union() {
            rounded_plate(plate_w, plate_d, 6, 8);
            translate([0, 0, 6]) rounded_plate(70, 70, 5, 6);   // deck flange riser
        }
        four_holes(56, 56, m3, 11);                              // matches deck intake
        // hook-loop pad is glued under; add grip dimples
        for (x = [-50, 0, 50], y = [-25, 25]) translate([x, y, 0]) translate([0,0,-0.5]) cylinder(d = 6, h = 2);
        // water dribble holes along the front edge
        for (x = [-40, 0, 40]) translate([x, plate_d/2 - 8, 0]) hole(2.5, 11);
    }
}
module water_tank() {                                            // ~200 ml, sits on the deck
    difference() {
        rounded_plate(120, 70, 70, 8);
        translate([0, 0, 4]) rounded_plate(120 - 2*4, 70 - 2*4, 70, 6);
        translate([45, 0, 60]) hole(28, 12);                    // fill port
        translate([0, -31, 8]) rotate([90,0,0]) translate([0,0,-4]) cylinder(d = 6, h = 8);  // pump outlet
    }
}
mop_plate();
translate([0, 120, 0]) water_tank();
