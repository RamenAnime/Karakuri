// Chest side panels, print 2. Passive grille plus a cable gland hole
// for the arm whip on each side.
include <common.scad>

module chest_side_panel() {
    difference() {
        rounded_plate(156, 132, 4, 8);
        for (y = [-40, -20, 0, 20, 40]) translate([0, y, 0]) slot(6, 90, 4);
        translate([60, -50, 0]) hole(16, 4);   // arm whip gland
        for (y = [-50, 0, 50]) for (sx = [-1, 1]) translate([sx * 70, y, 0]) hole(m3, 4);
    }
}
chest_side_panel();
