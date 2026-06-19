// Cable management clip, 8 mm bundle. Bolt one M3 through the deck or
// stick on a 3M pad. Print a dozen; the slicer fits many per plate.
include <common.scad>

module cable_clip() {
    difference() {
        union() {
            rounded_plate(22, 14, 3, 3);
            translate([4, 0, 0]) difference() {
                cylinder(d = 14, h = 12);
                translate([0, 0, 3]) cylinder(d = 9, h = 12);
                translate([0, -7, 3]) linear_extrude(12) square([5, 8]);
            }
        }
        translate([-7, 0, 0]) hole(m3, 3);
    }
}
cable_clip();
