import reflex as rx
import reflex_enterprise as rxe


CAROUSEL_LISTENERS = """
(() => {
  const scheduler = window.__vkCarouselScheduler || {timer: null, generation: 0};
  window.__vkCarouselScheduler = scheduler;
  window.__vkScheduleCarousel = (delay) => {
    const root = document.getElementById('vk-home-carousel');
    scheduler.generation += 1;
    const generation = scheduler.generation;
    window.clearTimeout(scheduler.timer);
    scheduler.timer = null;
    if (!root) return;
    scheduler.timer = window.setTimeout(() => {
      if (scheduler.generation !== generation) return;
      scheduler.timer = null;
      const currentRoot = document.getElementById('vk-home-carousel');
      const next = currentRoot && currentRoot.querySelector('#vk-slide-next');
      if (currentRoot && currentRoot.isConnected && next) next.click();
    }, delay);
  };
  window.__vkStopCarousel = () => {
    scheduler.generation += 1;
    window.clearTimeout(scheduler.timer);
    scheduler.timer = null;
  };
  const root = document.getElementById('vk-home-carousel');
  if (!root || root.dataset.gesturesReady) return;
  root.dataset.gesturesReady = 'true';
  const surface = root.querySelector('[data-carousel-surface]');
  let gesture = null;
  let suppressClick = false;
  const navigate = (direction) => root.querySelector(direction).click();
  surface.addEventListener('pointerdown', (event) => {
    if (!event.isPrimary || event.button !== 0 || event.target.closest('a, button')) return;
    suppressClick = false;
    gesture = {id: event.pointerId, x: event.clientX, y: event.clientY, dragging: false};
  });
  surface.addEventListener('pointermove', (event) => {
    if (!gesture || gesture.id !== event.pointerId) return;
    const dx = event.clientX - gesture.x;
    const dy = event.clientY - gesture.y;
    if (!gesture.dragging && Math.abs(dy) > 12 && Math.abs(dy) > Math.abs(dx)) {
      gesture = null;
      return;
    }
    if (!gesture.dragging && Math.abs(dx) > 12 && Math.abs(dx) > Math.abs(dy)) {
      gesture.dragging = true;
      surface.setPointerCapture(event.pointerId);
    }
  });
  surface.addEventListener('pointerup', (event) => {
    if (!gesture || gesture.id !== event.pointerId) return;
    const dx = event.clientX - gesture.x;
    const threshold = Math.min(80, Math.max(35, surface.clientWidth * 0.08));
    suppressClick = gesture.dragging;
    if (gesture.dragging && Math.abs(dx) >= threshold) {
      navigate(dx < 0 ? '#vk-slide-next' : '#vk-slide-previous');
    }
    gesture = null;
    if (surface.hasPointerCapture(event.pointerId)) surface.releasePointerCapture(event.pointerId);
  });
  const cancel = () => { gesture = null; };
  surface.addEventListener('pointercancel', cancel);
  surface.addEventListener('lostpointercapture', cancel);
  surface.addEventListener('click', (event) => {
    if (suppressClick) {
      event.preventDefault();
      event.stopPropagation();
      suppressClick = false;
    }
  }, true);
  root.addEventListener('keydown', (event) => {
    if (event.target.closest('input, textarea, select, [contenteditable]')) return;
    const controls = {
      ArrowLeft: '#vk-slide-previous', ArrowRight: '#vk-slide-next',
      Home: '#vk-slide-dot-0', End: '#vk-slide-dot-2'
    };
    if (controls[event.key]) {
      event.preventDefault();
      navigate(controls[event.key]);
    }
  });
})();
"""


class HeroState(rx.State):
    active_slide: int = 0
    autoplay_started: bool = False

    @rx.event
    def initialize_carousel(self):
        if self.autoplay_started:
            delay = 15000
        else:
            delay = 23000
            self.autoplay_started = True
        return rx.call_script(
            f"{CAROUSEL_LISTENERS}\nwindow.__vkScheduleCarousel({delay});"
        )

    @rxe.event(auth=False)
    def stop_carousel(self):
        return rx.call_script(
            "window.__vkStopCarousel && window.__vkStopCarousel();"
        )

    @rxe.event(auth=False)
    def previous_slide(self):
        self.active_slide = (self.active_slide - 1) % 3
        return rx.call_script(
            "window.__vkScheduleCarousel && window.__vkScheduleCarousel(15000);"
        )

    @rxe.event(auth=False)
    def next_slide(self):
        self.active_slide = (self.active_slide + 1) % 3
        return rx.call_script(
            "window.__vkScheduleCarousel && window.__vkScheduleCarousel(15000);"
        )

    @rxe.event(auth=False)
    def select_slide(self, index: int):
        if index in (0, 1, 2):
            self.active_slide = index
        return rx.call_script(
            "window.__vkScheduleCarousel && window.__vkScheduleCarousel(15000);"
        )
