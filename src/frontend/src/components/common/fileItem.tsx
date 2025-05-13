import * as React from "react";
import { FileItemProps } from "../../types/types";

export const FileItem: React.FC<FileItemProps> = ({ name, count, type, icon, details }) => {
  return (
    <div className="flex overflow-hidden gap-2 justify-center items-center p-2 w-full bg-white rounded border border-solid border-neutral-200">
      <div className="flex flex-1 shrink justify-between items-center self-stretch my-auto text-sm font-semibold leading-5 basis-0 min-h-[24px] min-w-[240px] text-[NeutralForeground1.Rest]">
        <div className="flex flex-1 shrink gap-1 items-center self-stretch my-auto w-full basis-0 min-h-[24px] min-w-[240px]">
          <img loading="lazy" src={icon} alt="" className="object-contain shrink-0 self-stretch my-auto w-5 aspect-square" />
          <div className="flex-1 shrink self-stretch my-auto basis-0 text-ellipsis">
            {name}
          </div>
        </div>
      </div>
      {count !== undefined && (
        <div className="flex gap-1 items-center self-stretch my-auto whitespace-nowrap">
          <div className="self-stretch my-auto text-xs font-semibold leading-4 text-right text-[NeutralForeground1.Rest]">
            {count}
          </div>
          <div className={`flex gap-1 items-center self-stretch my-auto w-4 text-base ${type === 'error' ? 'text-red-700' : 'text-yellow-600'} uppercase`}>
            <div className="self-stretch my-auto w-4 min-h-[16px]"></div>
          </div>
        </div>
      )}
    </div>
  );
};