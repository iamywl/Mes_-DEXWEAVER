/**
 * Toast notification hook — global toast state via Zustand.
 */
import { create } from 'zustand';

const useToastStore = create((set) => ({
  toast: null,
  showToast: (msg, ok = true) => {
    set({toast: {msg, ok}});
    setTimeout(() => set({toast: null}), 3000);
  },
}));

export const useToast = () => {
  const {toast, showToast} = useToastStore();
  return {toast, showToast};
};

export const Toast = () => {
  const {toast} = useToastStore();
  if (!toast) return null;
  return (
    <div className={`fixed top-6 right-6 z-[60] px-5 py-3 rounded-xl text-xs font-bold shadow-lg border ${
      toast.ok
        ? 'bg-emerald-900/90 border-emerald-700 text-emerald-300'
        : 'bg-red-900/90 border-red-700 text-red-300'
    }`}>
      {toast.msg}
    </div>
  );
};
