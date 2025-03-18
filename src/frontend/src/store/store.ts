import { configureStore } from '@reduxjs/toolkit';
import { batchSlice, fileReducer } from '../slices/batchSlice';
import authReducer from '../slices/authSlice';
import historyPanelReducer from '../slices/historyPanelSlice';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        batch: batchSlice.reducer,
        fileUpload: fileReducer,
        historyPanel: historyPanelReducer,
    },
})

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
