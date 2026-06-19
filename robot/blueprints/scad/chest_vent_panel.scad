// Front and rear chest panels, print 2. Each carries an 80 mm Noctua
// (NF-A8 class, 71.5 mm bolt square): front panel mounts its fan low
// as intake, rear panel mounts it high as exhaust, so air washes
// diagonally up across the computer and power boards. Flat, no supports.
include <common.scad>

module chest_vent_panel() {
    difference() {
        rounded_plate(176, 132, 4, 8);
        // fan bore and bolts, offset low; flip the panel for the high exhaust
        translate([0, -18, 0]) { hole(77, 4); four_holes(71.5, 71.5, m4, 4); }
        // grille slots above the fan zone
        for (x = [-60, -40, -20, 0, 20, 40, 60]) translate([x, 44, 0]) slot(6, 26, 4);
        // perimeter screws to the rings
        for (x = [-60, -20, 20, 60]) for (sy = [-1, 1]) translate([x, sy * 60, 0]) hole(m3, 4);
    }
}
chest_vent_panel();
