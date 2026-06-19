// Encoder cap: snaps an AS5600 board over a joint with the diametric
// magnet centred on the servo output axis. The magnet (6 x 2.5 mm
// diametric) glues into the spinning cup that screws to the horn disc;
// the stator ring holds the AS5600 board 1.5 mm above it on the fixed
// side. Print one cup and one ring per measured joint, 12 sets covers
// both legs, the waist, and one arm. Flat, no supports.
include <common.scad>

module magnet_cup() {
    difference() {
        cylinder(d = 18, h = 6);
        translate([0, 0, 3]) cylinder(d = 6.2, h = 4);     // magnet pocket
        for (a = [0, 90, 180, 270]) rotate([0, 0, a]) translate([7, 0, 0]) hole(2.6, 3);
    }
}
module stator_ring() {
    difference() {
        union() { cylinder(d = 34, h = 3); translate([0, 0, 3]) cylinder(d = 34, h = 6); }
        translate([0, 0, -0.5]) cylinder(d = 20, h = 10);   // clears the cup
        translate([0, 0, 3]) linear_extrude(7)              // AS5600 board seat
            square([19, 19], center = true);
        for (a = [45, 225]) rotate([0, 0, a]) translate([13, 0, 0]) hole(2.4, 9);
    }
}
magnet_cup(); translate([40, 0, 0]) stator_ring();
