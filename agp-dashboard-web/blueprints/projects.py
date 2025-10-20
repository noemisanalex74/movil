from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Project
from forms import ProjectForm

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

@projects_bp.route('/')
def projects_manager():
    # Query all projects from the database
    projects = Project.query.order_by(Project.last_modified.desc()).all()
    # TODO: Re-implement task counting once tasks are also in the database
    for project in projects:
        project.total_tasks = 0
        project.completed_tasks = 0
        project.progreso = 0
    return render_template('projects.html', proyectos=projects)

@projects_bp.route('/add', methods=['GET', 'POST'])
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project = Project(
            name=form.name.data,
            description=form.description.data,
            path=form.path.data,
            status=form.status.data
        )
        db.session.add(new_project)
        db.session.commit()
        flash('Proyecto aÃ±adido con Ã©xito.', 'success')
        return redirect(url_for('projects.projects_manager'))
    return render_template('project_form.html', form=form, title='AÃ±adir Proyecto')

@projects_bp.route('/edit/<project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.path = form.path.data
        project.status = form.status.data
        db.session.commit()
        flash('Proyecto actualizado con Ã©xito.', 'success')
        return redirect(url_for('projects.projects_manager'))
    return render_template('project_form.html', form=form, title='Editar Proyecto', project=project)

@projects_bp.route('/delete/<project_id>', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Proyecto eliminado con Ã©xito.', 'success')
    return redirect(url_for('projects.projects_manager'))
