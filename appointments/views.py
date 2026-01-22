from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q 
from .models import DaySchedule, Appointment, CustomUser
from .forms import ClientBookingForm
import sys


# --- PORTADA (LANDING PAGE) ---
def landing_page(request):
    return render(request, 'appointments/landing.html')

# --- VISTA DEL CALENDARIO (PRINCIPAL) ---
def booking_calendar(request):
    now = timezone.localtime(timezone.now())
    today_date = now.date()
    current_time_now = now.time()

    # TRADUCTOR MANUAL PARA ASEGURAR ESPAÑOL SIEMPRE
    dias_espanol = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    days_list = []
    
    # Configuración General
    SLOT_DURATION = 20
    LUNCH_DURATION_MINUTES = 60

    for i in range(5):
        loop_date = today_date + timedelta(days=i)
        day_schedule = DaySchedule.objects.filter(date=loop_date).first()
        
        # 1. Valores por defecto (8 AM - 6 PM)
        is_working = True
        start_time = time(8, 0)
        end_time = time(18, 0)
        lunch_active = False
        lunch_start = time(13, 0)
        lunch_end = time(14, 0)
        note = None

        if day_schedule:
            is_working = day_schedule.is_working_day
            start_time = day_schedule.start_time
            end_time = day_schedule.end_time
            lunch_active = day_schedule.is_lunch_break_active
            note = day_schedule.note
            
            if lunch_active:
                lunch_start = day_schedule.lunch_start_time
                dummy = datetime.combine(date.today(), lunch_start)
                lunch_end = (dummy + timedelta(minutes=LUNCH_DURATION_MINUTES)).time()

        # 2. Determinar Estado Inicial
        status = "DISPONIBLE"
        
        if not is_working:
            status = "DESCANSO"
        
        # Si ya pasó la hora de cierre (Solo aplica si es hoy)
        elif loop_date == today_date and current_time_now >= end_time:
            status = "TERMINADO"

        # 3. CÁLCULO DE CUPOS (Si está abierto y no ha terminado)
        elif status == "DISPONIBLE":
            taken_slots = Appointment.objects.filter(
                date=loop_date,
                status__in=['CONFIRMED', 'PENDING', 'RESCHEDULED']
            ).values_list('time', flat=True)

            slots_available = 0
            current_iter = datetime.combine(loop_date, start_time)
            
            while current_iter.time() < end_time:
                slot_t = current_iter.time()
                slot_end_dt = current_iter + timedelta(minutes=SLOT_DURATION)
                slot_end_t = slot_end_dt.time()

                if slot_end_t > end_time: break

                # Filtros
                is_past = (loop_date == today_date and slot_t <= current_time_now)
                
                is_lunch = False
                if lunch_active:
                    if (slot_t >= lunch_start and slot_t < lunch_end) or \
                       (slot_end_t > lunch_start and slot_end_t <= lunch_end):
                        is_lunch = True
                
                is_taken = slot_t in taken_slots

                if not is_past and not is_lunch and not is_taken:
                    slots_available += 1
                    break 
                
                current_iter += timedelta(minutes=SLOT_DURATION)
            
            if slots_available == 0:
                status = "AGOTADO"

        # AQUÍ USAMOS EL TRADUCTOR MANUAL
        nombre_dia = dias_espanol[loop_date.weekday()]

        days_list.append({
            'date': loop_date,
            'status': status,
            'day_name': nombre_dia, 
            'note': note
        })

    context = {'days_list': days_list}
    return render(request, 'appointments/calendar.html', context)

# --- API PARA OBTENER HORAS (AJAX) ---
def get_available_hours(request):
    try:
        date_str = request.GET.get('date')
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # --- CONFIGURACIÓN ---
        SLOT_DURATION = 20  
        LUNCH_DURATION_MINUTES = 60 
        
        start_time = time(8, 0)   # 8:00 AM
        end_time = time(18, 0)    # 6:00 PM
        lunch_active = False
        lunch_start = time(13, 0) # 1:00 PM
        lunch_end = time(14, 0)

        # 1. Configuración DB
        schedule = DaySchedule.objects.filter(date=selected_date).first()
        
        if schedule:
            if not schedule.is_working_day:
                return JsonResponse({'morning': [], 'noon': [], 'afternoon': [], 'evening': []}) 
            
            start_time = schedule.start_time
            end_time = schedule.end_time
            lunch_active = schedule.is_lunch_break_active
            
            if lunch_active:
                lunch_start = schedule.lunch_start_time
                dummy_date = datetime.combine(date.today(), lunch_start)
                lunch_end = (dummy_date + timedelta(minutes=LUNCH_DURATION_MINUTES)).time()

        # 2. Citas ocupadas
        existing_appointments = Appointment.objects.filter(
            date=selected_date,
            status__in=['CONFIRMED', 'PENDING', 'RESCHEDULED'] 
        ).values_list('time', flat=True)

        morning_slots = []
        noon_slots = []      
        afternoon_slots = []
        evening_slots = []
        
        current_time_iter = datetime.combine(selected_date, start_time)
        now = timezone.localtime(timezone.now())

        while current_time_iter.time() < end_time:
            slot_start = current_time_iter.time()
            slot_end_datetime = current_time_iter + timedelta(minutes=SLOT_DURATION)
            slot_end = slot_end_datetime.time()
            
            if slot_end > end_time:
                break

            # Filtros
            if selected_date == now.date() and slot_start <= now.time():
                current_time_iter += timedelta(minutes=SLOT_DURATION)
                continue

            is_lunch_time = False
            if lunch_active:
                if (slot_start >= lunch_start) and (slot_start < lunch_end):
                    is_lunch_time = True
                elif (slot_end > lunch_start) and (slot_end <= lunch_end):
                    is_lunch_time = True

            is_taken = slot_start in existing_appointments

            if not is_lunch_time and not is_taken:
                formatted_time = current_time_iter.strftime("%I:%M %p")
                
                if slot_start.hour < 12:
                    morning_slots.append(formatted_time)
                elif slot_start.hour == 12: 
                    noon_slots.append(formatted_time)
                elif 12 < slot_start.hour < 18: 
                    afternoon_slots.append(formatted_time)
                else: 
                    evening_slots.append(formatted_time)

            current_time_iter += timedelta(minutes=SLOT_DURATION)

        return JsonResponse({
            'morning': morning_slots,
            'noon': noon_slots,
            'afternoon': afternoon_slots,
            'evening': evening_slots
        })

    except Exception as e:
        print(f"Error en get_available_hours: {e}")
        return JsonResponse({'morning': [], 'noon': [], 'afternoon': [], 'evening': []})


# --- GUARDAR CITA (POST) ---
def book_appointment(request, date_str, time_str):
    try:
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        appointment_time = datetime.strptime(time_str, "%I:%M %p").time()
    except ValueError:
        return redirect('booking_calendar')

    if request.method == 'POST':
        form = ClientBookingForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone_number']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            nickname = form.cleaned_data['nickname']
            pin = form.cleaned_data['pin']

            user, created = CustomUser.objects.get_or_create(
                phone_number=phone,
                defaults={
                    'first_name': first_name, 
                    'last_name': last_name,
                    'nickname': nickname,
                    'security_pin': pin,
                    'role': 'CLIENT'
                }
            )

            user.first_name = first_name
            user.last_name = last_name
            user.security_pin = pin 
            user.nickname = nickname 
            user.save()

            appointment, created = Appointment.objects.get_or_create(
                client=user,
                date=appointment_date,
                time=appointment_time,
                defaults={'status': 'PENDING'}
            )

            if created:
                return redirect('booking_success')
            else:
                messages.error(request, "Ese horario ya fue reservado.")

    else:
        form = ClientBookingForm()

    context = {
        'form': form,
        'date_str': date_str, 
        'time': time_str,
        'date_obj': appointment_date 
    }
    return render(request, 'appointments/book_appointment.html', context)

def booking_success(request):
    return render(request, 'appointments/success.html')


# ==========================================
#     NUEVAS FUNCIONES: GESTIÓN DE CITAS (CLIENTE)
# ==========================================

def my_appointments(request):
    appointments = []
    search_performed = False 
    
    if request.method == 'POST':
        phone = request.POST.get('full_phone')
        input_pin = request.POST.get('pin') 
        search_performed = True
        
        if phone and input_pin:
            user = CustomUser.objects.filter(phone_number=phone).first()
            
            if user and user.security_pin == input_pin:
                now = timezone.localtime(timezone.now())
                cutoff_time = (now - timedelta(minutes=20)).time()
                
                appointments = Appointment.objects.filter(
                    client=user,
                    status__in=['PENDING', 'CONFIRMED']
                ).filter(
                    Q(date__gt=now.date()) | 
                    Q(date=now.date(), time__gt=cutoff_time)
                ).order_by('date', 'time')
                
            else:
                messages.error(request, 'Teléfono o PIN incorrectos.')

    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments,
        'search_performed': search_performed
    })

@require_POST
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    messages.success(request, 'Tu cita ha sido cancelada correctamente.')
    return redirect('my_appointments')

@require_POST
def postpone_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    new_time_str = request.POST.get('new_time')
    
    if new_time_str:
        try:
            new_time = datetime.strptime(new_time_str, '%I:%M %p').time()
            
            is_taken = Appointment.objects.filter(
                date=appointment.date, 
                time=new_time
            ).exclude(id=appointment.id).exists()
            
            if not is_taken:
                appointment.time = new_time
                appointment.save()
                messages.success(request, f'Cita movida exitosamente a las {new_time_str}.')
            else:
                messages.error(request, 'Ese horario ya fue ocupado por otra persona.')
                
        except ValueError:
             messages.error(request, 'Formato de hora inválido.')
    else:
        messages.error(request, 'Hubo un error al seleccionar la hora.')
        
    return redirect('my_appointments')


# ==========================================
#      ZONA DEL BARBERO (ADMINISTRACIÓN)
# ==========================================

def barber_login(request):
    if request.session.get('is_barber'):
        return redirect('barber_dashboard')

    if request.method == 'POST':
        pin = request.POST.get('pin')
        # CAMBIO: PIN de 6 dígitos
        if pin == '192837': 
            request.session['is_barber'] = True
            messages.success(request, '¡Bienvenido, Jefe!')
            return redirect('barber_dashboard')
        else:
            messages.error(request, 'PIN incorrecto. Acceso denegado.')

    return render(request, 'appointments/barber_login.html')

def barber_dashboard(request):
    if not request.session.get('is_barber'):
        return redirect('barber_login')

    now = timezone.localtime(timezone.now())
    today = now.date()
    
    appointments = Appointment.objects.filter(
        date=today
    ).exclude(status='CANCELLED').order_by('time')

    total_count = appointments.count()
    pending_count = appointments.filter(status='PENDING').count()

    return render(request, 'appointments/barber_dashboard.html', {
        'appointments': appointments,
        'today': today,
        'total_count': total_count,
        'pending_count': pending_count
    })

def barber_logout(request):
    request.session.flush()
    return redirect('barber_login')

# --- ACCIONES DE LOS BOTONES (DASHBOARD) ---

@require_POST
def mark_completed(request, appointment_id):
    if not request.session.get('is_barber'): return redirect('barber_login')
    
    app = get_object_or_404(Appointment, id=appointment_id)
    app.status = 'COMPLETED'
    app.save()
    
    messages.success(request, f'¡Listo! Corte de {app.client.first_name} registrado.')
    return redirect('barber_dashboard')

@require_POST
def mark_noshow(request, appointment_id):
    if not request.session.get('is_barber'): return redirect('barber_login')
    
    app = get_object_or_404(Appointment, id=appointment_id)
    app.status = 'NOSHOW'
    app.save()
    
    messages.warning(request, f'{app.client.first_name} marcado como NO ASISTIÓ.')
    return redirect('barber_dashboard')

# --- CONFIGURACIÓN DE HORARIOS ---

def barber_settings(request):
    if not request.session.get('is_barber'): return redirect('barber_login')
    
    now = timezone.localtime(timezone.now())
    today = now.date()
    week_schedule = []
    
    for i in range(7): 
        date_loop = today + timedelta(days=i)
        
        schedule, created = DaySchedule.objects.get_or_create(
            date=date_loop,
            defaults={
                'is_working_day': True,
                'start_time': time(8, 0),  # 8:00 AM
                'end_time': time(18, 0),   # 6:00 PM
                'is_lunch_break_active': False,
                'lunch_start_time': time(13, 0)
            }
        )
        week_schedule.append(schedule)

    return render(request, 'appointments/barber_settings.html', {
        'week_schedule': week_schedule
    })

@require_POST
def update_schedule(request, schedule_id):
    if not request.session.get('is_barber'): return redirect('barber_login')
    
    schedule = get_object_or_404(DaySchedule, id=schedule_id)
    
    schedule.is_working_day = request.POST.get('is_working') == 'on'
    schedule.note = request.POST.get('note', '').strip()
    schedule.is_lunch_break_active = request.POST.get('lunch_active') == 'on'
    
    try:
        st_str = request.POST.get('start_time')
        if st_str:
            schedule.start_time = datetime.strptime(st_str, '%H:%M').time()
            
        et_str = request.POST.get('end_time')
        if et_str:
            schedule.end_time = datetime.strptime(et_str, '%H:%M').time()
            
        if schedule.is_lunch_break_active:
             lt_str = request.POST.get('lunch_start')
             if lt_str:
                 schedule.lunch_start_time = datetime.strptime(lt_str, '%H:%M').time()
             
        schedule.save()
        
        status_msg = "Abierto" if schedule.is_working_day else "Cerrado"
        messages.success(request, f'Día {schedule.date.strftime("%d/%m")} actualizado: {status_msg}.')
        
    except ValueError:
        messages.error(request, 'Error en el formato de hora.')

    return redirect('barber_settings')