from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class ProjectForm(FlaskForm):
    """Form for adding and editing projects."""
    name = StringField(
        'Nombre del Proyecto',
        validators=[DataRequired(), Length(min=3, max=150)]
    )
    description = TextAreaField(
        'DescripciÃ³n',
        validators=[Optional(), Length(max=5000)]
    )
    path = StringField(
        'Ruta del Proyecto',
        validators=[Optional(), Length(max=255)]
    )
    status = SelectField(
        'Estado',
        choices=[
            ('nuevo', 'Nuevo'),
            ('en_desarrollo', 'En Desarrollo'),
            ('en_produccion', 'En ProducciÃ³n'),
            ('archivado', 'Archivado')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Guardar Proyecto')
