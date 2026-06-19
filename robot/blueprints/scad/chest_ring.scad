// Chest frame ring, print 2 (top and bottom). Internal bay 166 x 146
// swallows a Mac mini class computer (127 x 127 x 50) with room for
// power boards beside it. Corner posts bolt the rings together; vent
// and side panels hang on the M3 perimeter holes. 50 mm M4 squares:
// bottom centre to the waist disc, top centre to the head pan base,
// and one each side for the shoulder joints.
include <common.scad>

module chest_ring() {
    difference() {
        rounded_plate(190, 170, 8, 10);
        rounded_plate(166, 146, 8, 6);
        // corner post bolts
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 82, sy * 72, 0]) hole(m4, 8);
        // panel screw perimeter
        for (x = [-60, -20, 20, 60]) for (sy = [-1, 1]) translate([x, sy * 79, 0]) hole(m3, 8);
        for (y = [-50, 0, 50]) for (sx = [-1, 1]) translate([sx * 89, y, 0]) hole(m3, 8);
    }
    // centre bridge with the 50 mm square (waist below, head above)
    difference() {
        translate([0, 0, 0]) rounded_plate(70, 170, 8, 6);
        four_holes(50, 50, m4, 8);
        for (y = [-60, 60]) translate([0, y, 0]) hole(30, 8);   // cable pass
    }
}
chest_ring();
