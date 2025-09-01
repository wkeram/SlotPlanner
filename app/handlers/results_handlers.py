"""Results and scheduling event handlers.

This module contains handlers for schedule creation and export functionality.
"""

from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QTextEdit, QComboBox, QProgressBar, QLabel
from PySide6.QtCore import QThread, Signal, QTimer
from datetime import datetime, timedelta
import traceback
import os

try:
    from ortools.sat.python import cp_model

    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    cp_model = None

from app.config.logging_config import get_logger
from app.storage import Storage
from app.utils import show_error
from app.ui_teachers import refresh_teacher_table, refresh_children_table, refresh_tandems_table
from .base_handler import BaseHandler

logger = get_logger(__name__)


def results_create_schedule(window: QWidget, storage: Storage) -> None:
    """Create the optimized schedule using constraint solver.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _create_schedule():
        if not ORTOOLS_AVAILABLE:
            show_error(
                "OR-Tools is not installed. Schedule optimization requires OR-Tools.\n\n"
                "Please install with: pip install ortools",
                window,
            )
            return

        logger.info("Starting schedule creation with OR-Tools")

        # Show progress and status
        if hasattr(window, "feedback_manager") and window.feedback_manager:
            window.feedback_manager.show_status("Preparing schedule optimization...", show_progress=True)

        # Get current data
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()

        teachers = data.get("teachers", {})
        children = data.get("children", {})
        tandems = data.get("tandems", {})
        weights = data.get("weights", {})

        if not teachers or not children:
            show_error("Cannot create schedule: No teachers or children defined.", window)
            if hasattr(window, "feedback_manager") and window.feedback_manager:
                window.feedback_manager.show_error("Schedule creation failed - missing data")
            return

        # Create and run solver
        try:
            start_time = datetime.now()
            schedule, violations = create_optimized_schedule(teachers, children, tandems, weights)
            end_time = datetime.now()

            # Prepare optimization info
            optimization_info = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "runtime_seconds": (end_time - start_time).total_seconds(),
                "solver_status": "optimal" if not violations else "feasible",
                "teachers_count": len(teachers),
                "children_count": len(children),
                "tandems_count": len(tandems),
            }

            # Save schedule result with timestamp
            schedule_id = storage.save_schedule_result(year, schedule, violations, weights, optimization_info)

            if schedule_id:
                logger.info(f"Schedule {schedule_id} created with {len(violations)} violations")

                # Update results display
                _display_schedule_results(window, schedule, violations)

                # Refresh the schedule history dropdown
                from .main_handlers import _load_schedule_results_for_year

                _load_schedule_results_for_year(window, storage, year)

                if hasattr(window, "feedback_manager") and window.feedback_manager:
                    window.feedback_manager.show_success(
                        f"Schedule created successfully ({len(violations)} violations)"
                    )

                BaseHandler.show_info(
                    window,
                    "Schedule Created",
                    f"Optimization completed!\n\n"
                    f"Schedule ID: {schedule_id}\n"
                    f"Runtime: {optimization_info['runtime_seconds']:.2f} seconds\n"
                    f"Violations: {len(violations)}\n\n"
                    f"Check the Results tab for details.",
                )
            else:
                logger.error("Failed to save schedule results")
                show_error("Failed to save schedule results", window)

        except Exception as e:
            logger.error(f"Schedule creation failed: {e}")
            logger.error(traceback.format_exc())
            show_error(f"Schedule creation failed: {str(e)}", window)

            if hasattr(window, "feedback_manager") and window.feedback_manager:
                window.feedback_manager.show_error("Schedule creation failed")

    BaseHandler.safe_execute(_create_schedule, parent=window)


def results_export_pdf(window: QWidget, storage: Storage) -> None:
    """Export the current schedule to PDF.

    Args:
        window: Main application window instance
        storage: Storage instance for data persistence
    """

    def _export_pdf():
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
        except ImportError:
            show_error(
                "ReportLab is not installed. PDF export requires ReportLab.\n\n"
                "Please install with: pip install reportlab",
                window,
            )
            return

        logger.info("Starting PDF export")

        # Get current data
        year = window.ui.findChild(QComboBox, "comboYearSelect").currentText()
        data = storage.load(year) or storage.get_default_data_structure()

        schedule = data.get("schedule", {})
        if not schedule:
            show_error("No schedule to export. Please create a schedule first.", window)
            return

        # Show progress
        if hasattr(window, "feedback_manager") and window.feedback_manager:
            window.feedback_manager.show_status("Generating PDF export...", show_progress=True)

        try:
            # Create exports directory if it doesn't exist
            import os

            exports_dir = "exports"
            if not os.path.exists(exports_dir):
                os.makedirs(exports_dir)
                logger.info(f"Created exports directory: {exports_dir}")

            # Generate PDF with full path
            filename = f"SlotPlanner_Schedule_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            full_path = os.path.join(exports_dir, filename)
            generate_schedule_pdf(data, full_path)

            logger.info(f"PDF exported successfully: {full_path}")

            if hasattr(window, "feedback_manager") and window.feedback_manager:
                window.feedback_manager.show_success(f"PDF exported: {filename}")

            BaseHandler.show_info(
                window,
                "PDF Export Successful",
                f"Schedule has been exported to:\n{full_path}\n\n"
                f"The PDF contains individual teacher schedules, optimization weights, "
                f"detailed timing information, and violation summaries.",
            )

        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            logger.error(traceback.format_exc())
            show_error(f"PDF export failed: {str(e)}", window)

            if hasattr(window, "feedback_manager") and window.feedback_manager:
                window.feedback_manager.show_error("PDF export failed")

    BaseHandler.safe_execute(_export_pdf, parent=window)


def create_optimized_schedule(teachers, children, tandems, weights):
    """Create an optimized schedule using OR-Tools constraint solver.

    Args:
        teachers: Dictionary of teacher data
        children: Dictionary of children data
        tandems: Dictionary of tandem data
        weights: Optimization weights

    Returns:
        Tuple of (schedule_dict, violations_list)
    """
    model = cp_model.CpModel()

    # Time slots: 15-minute intervals from 7:00 to 20:45
    time_slots = []
    for hour in range(7, 21):
        for minute in [0, 15, 30, 45]:
            time_slots.append(f"{hour:02d}:{minute:02d}")

    days = ["Mo", "Di", "Mi", "Do", "Fr"]

    # Decision variables: child assigned to teacher at specific time
    assignments = {}
    for child in children:
        for teacher in teachers:
            for day in days:
                for time_slot in time_slots:
                    var_name = f"assign_{child}_{teacher}_{day}_{time_slot}"
                    assignments[(child, teacher, day, time_slot)] = model.NewBoolVar(var_name)

    # Constraint: Each child gets exactly one 45-minute slot per week
    for child in children:
        child_slots = []
        for teacher in teachers:
            for day in days:
                for time_slot in time_slots:
                    # Check if this creates a valid 45-minute slot
                    if _is_valid_45min_slot(time_slot, time_slots):
                        child_slots.append(assignments[(child, teacher, day, time_slot)])

        if child_slots:
            model.Add(sum(child_slots) == 1)

    # Constraint: Teacher availability
    for teacher, teacher_data in teachers.items():
        availability = teacher_data.get("availability", {})

        for child in children:
            for day in days:
                for time_slot in time_slots:
                    # If teacher not available, can't be assigned
                    if not _teacher_available_at_time(teacher_data, day, time_slot):
                        model.Add(assignments[(child, teacher, day, time_slot)] == 0)

    # Constraint: Child availability
    for child, child_data in children.items():
        availability = child_data.get("availability", {})

        for teacher in teachers:
            for day in days:
                for time_slot in time_slots:
                    # If child not available, can't be assigned
                    if not _child_available_at_time(child_data, day, time_slot):
                        model.Add(assignments[(child, teacher, day, time_slot)] == 0)

    # Objective: Maximize weighted preferences
    objective_terms = []

    # Preferred teacher bonus
    preferred_weight = weights.get("preferred_teacher", 5)
    for child, child_data in children.items():
        preferred_teachers = child_data.get("preferred_teachers", [])
        for teacher in preferred_teachers:
            if teacher in teachers:
                for day in days:
                    for time_slot in time_slots:
                        if _is_valid_45min_slot(time_slot, time_slots):
                            objective_terms.append(preferred_weight * assignments[(child, teacher, day, time_slot)])

    # Early slot preference bonus
    early_weight = weights.get("priority_early_slot", 3)
    for child, child_data in children.items():
        if child_data.get("early_preference", False):
            for teacher in teachers:
                for day in days:
                    # Morning slots (before 12:00) get bonus
                    for time_slot in time_slots:
                        if time_slot < "12:00" and _is_valid_45min_slot(time_slot, time_slots):
                            objective_terms.append(early_weight * assignments[(child, teacher, day, time_slot)])

    # Tandem fulfillment bonus
    tandem_weight = weights.get("tandem_fulfilled", 4)
    for tandem_name, tandem_data in tandems.items():
        child1 = tandem_data.get("child1")
        child2 = tandem_data.get("child2")
        priority = tandem_data.get("priority", 5)

        if child1 in children and child2 in children:
            for teacher in teachers:
                for day in days:
                    for time_slot in time_slots:
                        if _is_valid_45min_slot(time_slot, time_slots):
                            # Both children assigned to same teacher at same time
                            tandem_var = model.NewBoolVar(f"tandem_{tandem_name}_{teacher}_{day}_{time_slot}")

                            # tandem_var is 1 only if both children are assigned
                            model.Add(tandem_var <= assignments[(child1, teacher, day, time_slot)])
                            model.Add(tandem_var <= assignments[(child2, teacher, day, time_slot)])
                            model.Add(
                                tandem_var
                                >= assignments[(child1, teacher, day, time_slot)]
                                + assignments[(child2, teacher, day, time_slot)]
                                - 1
                            )

                            objective_terms.append(tandem_weight * priority * tandem_var)

    # Set objective
    if objective_terms:
        model.Maximize(sum(objective_terms))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0  # 1 minute timeout

    status = solver.Solve(model)

    schedule = {}
    violations = []

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Extract schedule
        for day in days:
            schedule[day] = {}

        for child in children:
            for teacher in teachers:
                for day in days:
                    for time_slot in time_slots:
                        if solver.Value(assignments[(child, teacher, day, time_slot)]) == 1:
                            if day not in schedule:
                                schedule[day] = {}
                            if time_slot not in schedule[day]:
                                schedule[day][time_slot] = {"teacher": teacher, "children": []}
                            schedule[day][time_slot]["children"].append(child)

        # Check for violations
        violations = _check_schedule_violations(schedule, teachers, children, tandems)

        logger.info(f"Schedule created successfully with {len(violations)} violations")
    else:
        logger.error(f"Solver failed with status: {status}")
        violations.append("Solver could not find a feasible solution")

    return schedule, violations


def _is_valid_45min_slot(start_time, time_slots):
    """Check if a time slot can accommodate a 45-minute appointment."""
    try:
        start_idx = time_slots.index(start_time)
        # Need at least 3 x 15-minute slots for 45 minutes
        return start_idx + 2 < len(time_slots)
    except ValueError:
        return False


def _teacher_available_at_time(teacher_data, day, time_slot):
    """Check if teacher is available at specific day/time."""
    availability = teacher_data.get("availability", {})
    day_slots = availability.get(day, [])

    for start, end in day_slots:
        if start <= time_slot < end:
            return True
    return False


def _child_available_at_time(child_data, day, time_slot):
    """Check if child is available at specific day/time."""
    availability = child_data.get("availability", {})
    if not availability:  # No constraints means available all the time
        return True

    day_slots = availability.get(day, [])
    if not day_slots:  # No slots for this day means not available
        return False

    for start, end in day_slots:
        if start <= time_slot < end:
            return True
    return False


def _check_schedule_violations(schedule, teachers, children, tandems):
    """Check for constraint violations in the schedule."""
    violations = []

    # Check that all children are scheduled
    scheduled_children = set()
    for day_schedule in schedule.values():
        for time_data in day_schedule.values():
            scheduled_children.update(time_data.get("children", []))

    unscheduled = set(children.keys()) - scheduled_children
    for child in unscheduled:
        violations.append(f"Child '{child}' could not be scheduled")

    # Check tandem violations
    for tandem_name, tandem_data in tandems.items():
        child1 = tandem_data.get("child1")
        child2 = tandem_data.get("child2")

        tandem_scheduled = False
        for day_schedule in schedule.values():
            for time_data in day_schedule.values():
                children_in_slot = time_data.get("children", [])
                if child1 in children_in_slot and child2 in children_in_slot:
                    tandem_scheduled = True
                    break

        if not tandem_scheduled and child1 in scheduled_children and child2 in scheduled_children:
            violations.append(f"Tandem '{tandem_name}' could not be scheduled together")

    return violations


def _display_schedule_results(window, schedule, violations):
    """Display schedule results in the UI tables and violations text."""
    # Update schedule table
    schedule_table = window.ui.findChild(QTableWidget, "tableSchedule")
    if schedule_table:
        _populate_schedule_table(schedule_table, schedule)

    # Update violations text
    violations_text = window.ui.findChild(QTextEdit, "textViolations")
    if violations_text:
        if violations:
            violations_text.setPlainText("\n".join([f"• {v}" for v in violations]))
        else:
            violations_text.setPlainText("No constraint violations found. Perfect schedule!")


def _populate_schedule_table(table, schedule):
    """Populate the schedule table with enhanced assignment data showing time ranges and teacher grouping."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont

    # Collect all time slots and teachers
    all_times = set()
    all_teachers = set()
    for day_schedule in schedule.values():
        all_times.update(day_schedule.keys())
        for assignment in day_schedule.values():
            if assignment.get("teacher"):
                all_teachers.add(assignment.get("teacher"))

    sorted_times = sorted(all_times)
    days = ["Mo", "Di", "Mi", "Do", "Fr"]

    # Setup table
    table.setRowCount(len(sorted_times))
    table.setColumnCount(len(days) + 1)  # +1 for time range column

    headers = ["Time Range"] + days
    table.setHorizontalHeaderLabels(headers)

    # Create bold font for teacher names
    bold_font = QFont()
    bold_font.setBold(True)

    # Populate data
    for row, time_slot in enumerate(sorted_times):
        # Time range column - convert to 45-minute range
        time_range = _convert_to_time_range(time_slot)
        time_item = QTableWidgetItem(time_range)
        time_item.setFont(bold_font)
        table.setItem(row, 0, time_item)

        # Day columns with enhanced teacher grouping
        for col, day in enumerate(days):
            assignment_text = ""
            if day in schedule and time_slot in schedule[day]:
                assignment = schedule[day][time_slot]
                teacher = assignment.get("teacher", "")
                children = assignment.get("children", [])

                if teacher and children:
                    # Format: Teacher Name (bold) followed by children
                    assignment_text = f"👨‍🏫 {teacher}\n📚 {', '.join(children)}"
                elif teacher:
                    assignment_text = f"👨‍🏫 {teacher}\n(No children assigned)"
                elif children:
                    assignment_text = f"📚 {', '.join(children)}\n(No teacher assigned)"

            cell_item = QTableWidgetItem(assignment_text)

            # Style cells based on content
            if assignment_text:
                from PySide6.QtGui import QColor

                if "No teacher assigned" in assignment_text:
                    cell_item.setBackground(QColor(255, 255, 0))  # Yellow for missing teacher
                elif "No children assigned" in assignment_text:
                    cell_item.setBackground(QColor(211, 211, 211))  # Light gray for empty slots
                else:
                    cell_item.setBackground(QColor(144, 238, 144))  # Light green for complete assignments

            table.setItem(row, col + 1, cell_item)

    # Resize columns and rows for better visibility
    table.resizeRowsToContents()
    table.resizeColumnsToContents()

    # Set minimum column widths for better readability
    min_col_width = 150
    for col in range(table.columnCount()):
        current_width = table.columnWidth(col)
        if current_width < min_col_width:
            table.setColumnWidth(col, min_col_width)

    # Add teacher summary information at the end if there are teachers
    if all_teachers:
        summary_row = table.rowCount()
        table.insertRow(summary_row)

        # Add summary header
        from PySide6.QtGui import QColor

        summary_item = QTableWidgetItem(f"📊 Summary ({len(all_teachers)} teachers)")
        summary_item.setFont(bold_font)
        summary_item.setBackground(QColor(0, 0, 139))  # Dark blue
        summary_item.setForeground(QColor(255, 255, 255))  # White
        table.setItem(summary_row, 0, summary_item)

        # Add teacher list in remaining columns
        teachers_list = ", ".join(sorted(all_teachers))
        for col in range(1, table.columnCount()):
            teacher_summary_item = QTableWidgetItem(teachers_list if col == 1 else "")
            teacher_summary_item.setBackground(QColor(173, 216, 230))  # Light blue
            table.setItem(summary_row, col, teacher_summary_item)

        table.resizeRowsToContents()


def generate_schedule_pdf(data, filename):
    """Generate a comprehensive PDF report of the schedule."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5 * inch)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"], fontSize=24, spaceAfter=30, alignment=1  # Center
    )
    story.append(Paragraph("SlotPlanner - Weekly Schedule", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 20))

    # Summary statistics
    teachers = data.get("teachers", {})
    children = data.get("children", {})
    tandems = data.get("tandems", {})
    violations = data.get("violations", [])
    weights = data.get("weights", {})

    summary_data = [
        ["Teachers", str(len(teachers))],
        ["Children", str(len(children))],
        ["Tandems", str(len(tandems))],
        ["Violations", str(len(violations))],
    ]

    summary_table = Table(summary_data, colWidths=[2 * inch, 1 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    story.append(Paragraph("Schedule Summary", styles["Heading2"]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Optimization weights section
    story.append(Paragraph("Optimization Weights Used", styles["Heading2"]))
    if weights:
        weights_data = [["Weight Parameter", "Value", "Description"]]

        weight_descriptions = {
            "preferred_teacher": "Teacher preference priority",
            "priority_early_slot": "Early time slot preference",
            "tandem_fulfilled": "Tandem pairing importance",
            "teacher_pause_respected": "Teacher break time respect",
            "preserve_existing_plan": "Stability with previous schedule",
        }

        for key, value in weights.items():
            description = weight_descriptions.get(key, "Custom weight")
            weights_data.append([key.replace("_", " ").title(), str(value), description])

        weights_table = Table(weights_data, colWidths=[2.5 * inch, 0.7 * inch, 2.8 * inch])
        weights_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.lightblue),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("ALIGN", (1, 1), (1, -1), "CENTER"),  # Center the values column
                ]
            )
        )

        story.append(weights_table)
    else:
        story.append(Paragraph("No optimization weights data available.", styles["Normal"]))

    story.append(Spacer(1, 15))
    story.append(Spacer(1, 20))

    # Individual teacher schedules
    schedule = data.get("schedule", {})
    for teacher_name in sorted(teachers.keys()):
        story.append(PageBreak())
        story.append(Paragraph(f"Schedule for: {teacher_name}", styles["Heading2"]))

        # Create teacher's weekly schedule table
        days = ["Mo", "Di", "Mi", "Do", "Fr"]
        teacher_schedule = _extract_teacher_schedule(schedule, teacher_name)

        if teacher_schedule:
            times = sorted(teacher_schedule.keys())
            schedule_data = [["Time Range"] + days]

            for time_slot in times:
                # Convert single time point to 45-minute range
                time_range = _convert_to_time_range(time_slot)
                row = [time_range]
                for day in days:
                    children = teacher_schedule.get(time_slot, {}).get(day, [])
                    row.append(", ".join(children) if children else "")
                schedule_data.append(row)

            teacher_table = Table(schedule_data)
            teacher_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )

            story.append(teacher_table)
        else:
            story.append(Paragraph("No assignments for this teacher.", styles["Normal"]))

        story.append(Spacer(1, 20))

    # Violations summary
    if violations:
        story.append(PageBreak())
        story.append(Paragraph("Constraint Violations", styles["Heading2"]))
        for violation in violations:
            story.append(Paragraph(f"• {violation}", styles["Normal"]))

    # Generate PDF
    doc.build(story)
    logger.info(f"PDF generated: {filename}")


def _extract_teacher_schedule(schedule, teacher_name):
    """Extract a specific teacher's schedule from the full schedule."""
    teacher_schedule = {}

    for day, day_schedule in schedule.items():
        for time_slot, assignment in day_schedule.items():
            if assignment.get("teacher") == teacher_name:
                if time_slot not in teacher_schedule:
                    teacher_schedule[time_slot] = {}
                teacher_schedule[time_slot][day] = assignment.get("children", [])

    return teacher_schedule


def _convert_to_time_range(time_slot):
    """Convert a single time point to a 45-minute time range.

    Args:
        time_slot: Time in HH:MM format

    Returns:
        Time range string in format "HH:MM–HH:MM"
    """
    try:
        from datetime import datetime, timedelta

        # Parse the start time
        start_time = datetime.strptime(time_slot, "%H:%M")

        # Add 45 minutes for the end time
        end_time = start_time + timedelta(minutes=45)

        # Format as range
        return f"{start_time.strftime('%H:%M')}–{end_time.strftime('%H:%M')}"

    except ValueError:
        # If parsing fails, return the original time slot
        logger.warning(f"Could not parse time slot: {time_slot}")
        return time_slot
