// Tibia: 80 mm lower leg from the knee horn to a rubber foot. The
// foot socket takes a 16 mm rubber chair tip from any hardware aisle.
// Print 4 flat, no supports.
include <servo_common.scad>

tibia = 80;

module leg_tibia() {
    difference() {
        union() {
            hull() {
                cylinder(d = servo_horn_circle + 10, h = 6);
                translate([tibia, 0, 0]) cylinder(d = 18, h = 6);
            }
            translate([tibia, 0, 0]) cylinder(d = 16, h = 18);
        }
        horn_holes(6);
        for (x = [28, 50]) translate([x, 0, 0]) hole(9, 6);
    }
}
leg_tibia();
