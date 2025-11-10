from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database.db import db, User, Analysis, Team, TeamMember, Annotation
from flask_socketio import emit, join_room, leave_room
import json
from datetime import datetime

collaboration = Blueprint('collaboration', __name__)

@collaboration.route('/teams')
@login_required
def teams():
    """Display user's teams"""
    user_teams = Team.query.join(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    return render_template('teams.html', teams=user_teams)

@collaboration.route('/team/create', methods=['GET', 'POST'])
@login_required
def create_team():
    """Create a new team"""
    if request.method == 'POST':
        team_name = request.form.get('team_name')
        
        if not team_name:
            flash('Team name is required', 'danger')
            return redirect(url_for('collaboration.create_team'))
        
        # Create new team
        new_team = Team(
            name=team_name,
            created_by=current_user.id
        )
        db.session.add(new_team)
        db.session.flush()
        
        # Add creator as admin
        team_member = TeamMember(
            team_id=new_team.id,
            user_id=current_user.id,
            role='admin'
        )
        db.session.add(team_member)
        db.session.commit()
        
        flash('Team created successfully', 'success')
        return redirect(url_for('collaboration.team_detail', team_id=new_team.id))
    
    return render_template('create_team.html')

@collaboration.route('/team/<int:team_id>')
@login_required
def team_detail(team_id):
    """Display team details and shared analyses"""
    team = Team.query.get_or_404(team_id)
    
    # Check if user is a member of the team
    is_member = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if not is_member:
        flash('You are not a member of this team', 'danger')
        return redirect(url_for('collaboration.teams'))
    
    team_members = TeamMember.query.filter_by(team_id=team_id).all()
    members = []
    for member in team_members:
        user = User.query.get(member.user_id)
        members.append({
            'id': user.id,
            'username': user.username,
            'role': member.role,
            'joined_at': member.joined_at
        })
    
    shared_analyses = Analysis.query.filter_by(team_id=team_id).all()
    
    return render_template('team_detail.html', team=team, members=members, analyses=shared_analyses, is_admin=(is_member.role == 'admin'))

@collaboration.route('/team/<int:team_id>/invite', methods=['POST'])
@login_required
def invite_member(team_id):
    """Invite a user to the team"""
    team = Team.query.get_or_404(team_id)
    
    # Check if user is an admin of the team
    is_admin = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id, role='admin').first()
    if not is_admin:
        flash('You do not have permission to invite members', 'danger')
        return redirect(url_for('collaboration.team_detail', team_id=team_id))
    
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('collaboration.team_detail', team_id=team_id))
    
    # Check if user is already a member
    existing_member = TeamMember.query.filter_by(team_id=team_id, user_id=user.id).first()
    if existing_member:
        flash('User is already a member of this team', 'warning')
        return redirect(url_for('collaboration.team_detail', team_id=team_id))
    
    # Add user to team
    new_member = TeamMember(
        team_id=team_id,
        user_id=user.id,
        role='member'
    )
    db.session.add(new_member)
    db.session.commit()
    
    flash('User added to team successfully', 'success')
    return redirect(url_for('collaboration.team_detail', team_id=team_id))

@collaboration.route('/analysis/<int:analysis_id>/share', methods=['POST'])
@login_required
def share_analysis(analysis_id):
    """Share an analysis with a team"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if user owns the analysis
    if analysis.user_id != current_user.id:
        flash('You do not have permission to share this analysis', 'danger')
        return redirect(url_for('dashboard'))
    
    team_id = request.form.get('team_id')
    team = Team.query.get_or_404(team_id)
    
    # Check if user is a member of the team
    is_member = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if not is_member:
        flash('You are not a member of this team', 'danger')
        return redirect(url_for('dashboard'))
    
    # Share analysis with team
    analysis.is_shared = True
    analysis.team_id = team_id
    db.session.commit()
    
    flash('Analysis shared with team successfully', 'success')
    return redirect(url_for('dashboard'))

@collaboration.route('/analysis/<int:analysis_id>/annotate', methods=['POST'])
@login_required
def add_annotation(analysis_id):
    """Add an annotation to an analysis"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if user has access to the analysis
    if analysis.user_id != current_user.id and not (analysis.is_shared and TeamMember.query.filter_by(team_id=analysis.team_id, user_id=current_user.id).first()):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    content = data.get('content')
    timestamp = data.get('timestamp')
    x_position = data.get('x_position')
    y_position = data.get('y_position')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    annotation = Annotation(
        analysis_id=analysis_id,
        user_id=current_user.id,
        content=content,
        timestamp=timestamp,
        x_position=x_position,
        y_position=y_position
    )
    db.session.add(annotation)
    db.session.commit()
    
    # Get user info for response
    user = User.query.get(current_user.id)
    
    return jsonify({
        'id': annotation.id,
        'content': annotation.content,
        'timestamp': annotation.timestamp,
        'x_position': annotation.x_position,
        'y_position': annotation.y_position,
        'created_at': annotation.created_at.isoformat(),
        'user': {
            'id': user.id,
            'username': user.username
        }
    }), 201

@collaboration.route('/analysis/<int:analysis_id>/annotations')
@login_required
def get_annotations(analysis_id):
    """Get all annotations for an analysis"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if user has access to the analysis
    if analysis.user_id != current_user.id and not (analysis.is_shared and TeamMember.query.filter_by(team_id=analysis.team_id, user_id=current_user.id).first()):
        return jsonify({'error': 'Access denied'}), 403
    
    annotations = Annotation.query.filter_by(analysis_id=analysis_id).all()
    result = []
    
    for annotation in annotations:
        user = User.query.get(annotation.user_id)
        result.append({
            'id': annotation.id,
            'content': annotation.content,
            'timestamp': annotation.timestamp,
            'x_position': annotation.x_position,
            'y_position': annotation.y_position,
            'created_at': annotation.created_at.isoformat(),
            'user': {
                'id': user.id,
                'username': user.username
            }
        })
    
    return jsonify(result)

# Socket.IO event handlers for real-time collaboration
def register_socketio_events(socketio):
    @socketio.on('join_analysis_room')
    @login_required
    def handle_join_analysis_room(data):
        analysis_id = data.get('analysis_id')
        analysis = Analysis.query.get_or_404(analysis_id)
        
        # Check if user has access to the analysis
        if analysis.user_id != current_user.id and not (analysis.is_shared and TeamMember.query.filter_by(team_id=analysis.team_id, user_id=current_user.id).first()):
            return False
        
        room = f"analysis_{analysis_id}"
        join_room(room)
        
        emit('user_joined', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room=room)
    
    @socketio.on('leave_analysis_room')
    def handle_leave_analysis_room(data):
        analysis_id = data.get('analysis_id')
        room = f"analysis_{analysis_id}"
        leave_room(room)
        
        emit('user_left', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room=room)
    
    @socketio.on('new_annotation')
    def handle_new_annotation(data):
        analysis_id = data.get('analysis_id')
        content = data.get('content')
        timestamp = data.get('timestamp')
        x_position = data.get('x_position')
        y_position = data.get('y_position')
        
        analysis = Analysis.query.get_or_404(analysis_id)
        
        # Check if user has access to the analysis
        if analysis.user_id != current_user.id and not (analysis.is_shared and TeamMember.query.filter_by(team_id=analysis.team_id, user_id=current_user.id).first()):
            return False
        
        annotation = Annotation(
            analysis_id=analysis_id,
            user_id=current_user.id,
            content=content,
            timestamp=timestamp,
            x_position=x_position,
            y_position=y_position
        )
        db.session.add(annotation)
        db.session.commit()
        
        room = f"analysis_{analysis_id}"
        emit('annotation_added', {
            'id': annotation.id,
            'content': annotation.content,
            'timestamp': annotation.timestamp,
            'x_position': annotation.x_position,
            'y_position': annotation.y_position,
            'created_at': annotation.created_at.isoformat(),
            'user': {
                'id': current_user.id,
                'username': current_user.username
            }
        }, room=room)