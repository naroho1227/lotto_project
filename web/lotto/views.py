import json
import random
import functools
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import LottoDraw, LottoTicket


# - 헬퍼 함수 -

def _login_required(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def _admin_required(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


def _calc_rank(my_nums, win_nums, bonus):
    my_set  = set(my_nums)
    win_set = set(win_nums)
    matched = len(my_set & win_set)
    has_bonus = bonus in my_set

    if matched == 6:                    return 1
    if matched == 5 and has_bonus:      return 2
    if matched == 5:                    return 3
    if matched == 4:                    return 4
    if matched == 3:                    return 5
    return 0


def _next_draw_number():
    last = LottoDraw.objects.order_by('-draw_number').first()
    return (last.draw_number + 1) if last else 1


# ─ 인증 함수 ─

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    error = ''
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username', ''),
                            password=request.POST.get('password', ''))
        if user:
            login(request, user)
            return redirect('index')
        error = '아이디 또는 비밀번호가 올바르지 않습니다.'
    return render(request, 'lotto/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    error = ''
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if not username:
            error = '아이디를 입력하세요.'
        elif User.objects.filter(username=username).exists():
            error = '이미 사용 중인 아이디입니다.'
        elif len(password1) < 4:
            error = '비밀번호는 4자 이상이어야 합니다.'
        elif password1 != password2:
            error = '비밀번호가 일치하지 않습니다.'
        else:
            User.objects.create_user(username=username, password=password1)
            return redirect('login')
    return render(request, 'lotto/register.html', {'error': error})


# ─ 일반 사용자 함수 ─

@_login_required
def index(request):
    latest       = LottoDraw.objects.order_by('-draw_number').first()
    next_draw_no = _next_draw_number()
    return render(request, 'lotto/index.html', {
        'latest':       latest,
        'next_draw_no': next_draw_no,
    })


@_login_required
def buy_manual(request):
    next_draw_no = _next_draw_number()
    error = ''
    if request.method == 'POST':
        raw = [request.POST.get(f'n{i}', '') for i in range(1, 7)]
        try:
            nums = [int(x) for x in raw]
        except ValueError:
            error = '숫자를 모두 입력해주세요.'
            return render(request, 'lotto/buy_manual.html',
                        {'error': error, 'next_draw_no': next_draw_no})

        if len(set(nums)) != 6 or not all(1 <= n <= 45 for n in nums):
            error = '1~45 사이의 서로 다른 숫자 6개를 입력해주세요.'
            return render(request, 'lotto/buy_manual.html',
                        {'error': error, 'next_draw_no': next_draw_no})

        nums.sort()
        LottoTicket.objects.create(
            user=request.user,
            numbers=json.dumps(nums),
            is_auto=False,
        )
        messages.success(request,
            f'제 {next_draw_no}회차 수동 구매 완료. 번호: {nums}')
        return redirect('my_tickets')

    return render(request, 'lotto/buy_manual.html', {'next_draw_no': next_draw_no})


@_login_required
def buy_auto(request):
    next_draw_no = _next_draw_number()

    if request.method == 'POST':
        confirmed = request.POST.get('confirmed')
        if confirmed == 'yes':
            nums = sorted(random.sample(range(1, 46), 6))
            LottoTicket.objects.create(
                user=request.user,
                numbers=json.dumps(nums),
                is_auto=True,
            )
            messages.success(request,
                f'제 {next_draw_no}회차 자동 구매 완료. 번호: {nums}')
            return redirect('my_tickets')
        return redirect('index')

    return render(request, 'lotto/buy_auto_confirm.html',
                {'next_draw_no': next_draw_no})


@_login_required
def my_tickets(request):
    tickets = (LottoTicket.objects
                .filter(user=request.user)
                .select_related('draw')
                .order_by('-purchased_at'))
    return render(request, 'lotto/my_tickets.html', {'tickets': tickets})


@_login_required
def check(request):
    draws = LottoDraw.objects.order_by('-draw_number')
    result = None
    selected_draw = None

    if request.method == 'POST':
        draw_id = request.POST.get('draw_id')
        try:
            selected_draw = LottoDraw.objects.get(pk=draw_id)
        except LottoDraw.DoesNotExist:
            pass

        if selected_draw:
            tickets = LottoTicket.objects.filter(
                user=request.user, draw=selected_draw
            )
            result = []
            for t in tickets:
                rank = _calc_rank(t.get_numbers(),
                                selected_draw.get_numbers(),
                                selected_draw.bonus)
                result.append({'ticket': t, 'rank': rank})

    return render(request, 'lotto/check.html', {
        'draws':         draws,
        'result':        result,
        'selected_draw': selected_draw,
    })


# ─ 관리자 함수 ─

@_admin_required
def admin_sales(request):
    tickets = (LottoTicket.objects
                .select_related('user', 'draw')
                .order_by('-purchased_at'))
    return render(request, 'lotto/admin_sales.html', {'tickets': tickets})


@_admin_required
def admin_draw(request):
    message = ''
    error   = ''
    if request.method == 'POST':
        undrawn = LottoTicket.objects.filter(draw__isnull=True).exists()
        if not undrawn:
            error = '추첨할 티켓이 없습니다.'
        else:
            next_no = _next_draw_number()
            nums    = sorted(random.sample(range(1, 46), 6))
            pool    = list(range(1, 46))
            for n in nums:
                pool.remove(n)
            bonus   = random.choice(pool)
            draw    = LottoDraw.objects.create(
                draw_number=next_no,
                numbers=json.dumps(nums),
                bonus=bonus,
            )
            for ticket in LottoTicket.objects.filter(draw__isnull=True):
                rank = _calc_rank(ticket.get_numbers(), nums, bonus)
                ticket.draw = draw
                ticket.rank = rank if rank > 0 else None
                ticket.save()
            message = f'{next_no}회차 추첨 완료. 당첨번호: {nums}  보너스: {bonus}'

    draws = LottoDraw.objects.order_by('-draw_number')
    return render(request, 'lotto/admin_draw.html', {
        'draws':   draws,
        'message': message,
        'error':   error,
    })


@_admin_required
def admin_winners(request):
    tickets = (LottoTicket.objects
                .filter(rank__isnull=False, rank__gt=0)
                .select_related('user', 'draw')
                .order_by('rank', '-draw__draw_number'))
    return render(request, 'lotto/admin_winners.html', {'tickets': tickets})
