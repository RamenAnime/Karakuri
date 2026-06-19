// Riser block for a common 15 to 25 mm ball transfer or swivel caster.
// Height is parametric: set riser_h so the deck sits level once your
// wheels and motor mounts are installed. Default suits an 80 mm wheel
// with the JGA25 saddle mount and a CY-15H ball caster (15 mm ball).

include <common.scad>

riser_h = 24;

module caster_riser() {
    difference() {
        rounded_plate(40, 40, riser_h, 5);
        // Up to the deck
        four_holes(24, 24, m3, riser_h);
        // Caster mounting slots underneath, fits 20 to 30 mm patterns
        for (a = [0, 90])
            rotate([0, 0, a]) {
                translate([0, 12.5, 0]) slot(m3, 10, 8);
                translate([0, -12.5, 0]) slot(m3, 10, 8);
            }
    }
}

caster_riser();
