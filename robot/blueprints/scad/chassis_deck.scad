// KARAKURI chassis deck
// 200 x 200 main structural plate. Drive wheels mount mid-deck, ball
// caster at the front, mast at the rear, vacuum intake ahead of the
// wheel line, battery strap slots over the axle for a low centre of
// mass under the Kinect mast. Prints flat, no supports.

include <common.scad>

deck_x = 200;
deck_y = 200;
deck_t = 6;

module chassis_deck() {
    difference() {
        rounded_plate(deck_x, deck_y, deck_t, 12);

        // Motor mount slot grid, one cluster each side at the wheel line,
        // matching the mount base four_holes(40, 36): slots give tracking
        // adjustment along x
        for (side = [-1, 1], sx = [-1, 1], sy = [-1, 1])
            translate([side * 78 + sx * 20, sy * 18, 0]) slot(m3, 8, deck_t);

        // Front ball caster, 40 mm behind the front edge so the cliff
        // sensors at the edge trigger before the caster reaches a drop
        translate([0, 60, 0]) four_holes(24, 24, m3, deck_t);

        // Mast base at the rear, 4 x M4
        translate([0, -70, 0]) four_holes(50, 50, m4, deck_t);

        // Vacuum intake throat ahead of the wheel line
        translate([0, 32, 0]) hole(40, deck_t);
        translate([0, 32, 0]) four_holes(56, 56, m3, deck_t);

        // Battery strap slots straddling the axle line
        for (side = [-1, 1])
            translate([side * 34, -18, 0]) slot(4.5, 28, deck_t);

        // Electronics tray standoffs, rear quarter
        translate([0, -38, 0]) four_holes(110, 40, m3, deck_t);

        // Bumper standoff holes along the front edge
        for (x = [-70, 0, 70])
            translate([x, 92, 0]) hole(m3, deck_t);

        // Cliff sensor bracket holes: front corners and rear corners
        for (sx = [-1, 1]) {
            translate([sx * 80, 88, 0]) { hole(m3, deck_t); translate([0, -12, 0]) hole(m3, deck_t); }
            translate([sx * 80, -88, 0]) { hole(m3, deck_t); translate([0, 12, 0]) hole(m3, deck_t); }
        }

        // E-stop mount holes, rear edge beside the mast
        translate([62, -86, 0]) { hole(m4, deck_t); translate([0, 0, 0]) translate([0, 14, 0]) hole(m4, deck_t); }

        // Dock contact shoe under the front edge
        translate([0, 78, 0]) four_holes(84, 24, m3, deck_t);

        // Quadruped hip mounts, one per corner; the printed mount installs
        // rotated 90 degrees so its long axis runs along the deck edge and
        // the leg swings outboard
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * 78, sy * 70, 0]) four_holes(24, 54, m4, deck_t);

        // Arm turret base, forward of the mast
        translate([0, -10, 0]) four_holes(66, 66, m4, deck_t);
    }
}

chassis_deck();
