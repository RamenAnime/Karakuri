// Under-robot contact shoe. Two copper or brass strips screw into the
// channels, wired up through the deck to the charge port. Spacing
// matches the dock recesses at 60 mm. Bolts to the deck front
// underside with 4 x M3. Print flat.
include <common.scad>

module dock_contact_shoe() {
    difference() {
        rounded_plate(100, 44, 8, 5);
        four_holes(84, 32, m3, 8);
        for (x = [-30, 30]) {
            translate([x, 0, 8 - 3]) linear_extrude(4)
                square([14, 36], center = true);
            for (y = [-12, 12]) translate([x, y, 0]) hole(2.6, 8);
            // wire channel up through the plate
            translate([x, 14, 0]) hole(4, 8);
        }
    }
}
dock_contact_shoe();
