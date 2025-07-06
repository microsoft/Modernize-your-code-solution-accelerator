import * as React from "react";
import { ErrorWarningProps } from "../../types/types";

export const ErrorWarningSection: React.FC<ErrorWarningProps> = ({ title, count, type, items }) => {
  return (
    <div className="flex flex-col pb-4 mt-4 w-full rounded bg-neutral-50">
      <div className={`flex overflow-hidden flex-col justify-center p-2 w-full ${type === 'error' ? 'bg-red-100' : 'bg-orange-100'} rounded`}>
        <div className="flex flex-wrap gap-2 items-center w-full">
          <div className="flex-1 shrink gap-1 self-stretch my-auto text-sm font-semibold leading-5 min-w-[240px] text-zinc-900">
            {title} ({count})
          </div>
          <div className="flex justify-center items-center self-stretch px-0.5 my-auto w-6 h-6 rounded bg-white bg-opacity-0">
            <div className="flex gap-1 justify-center items-center self-stretch my-auto w-5">
              <img loading="lazy" src="https://cdn.builder.io/api/v1/image/assets/7fd5ec0079584b17bc43d5c78eb1268d/92432d0bb350d91e18eaad8e7af40adab5dfad0b556300ef18e9b3f43faf8da5?apiKey=7fd5ec0079584b17bc43d5c78eb1268d&" alt="" className="object-contain self-stretch my-auto w-5 aspect-square" />
            </div>
          </div>
        </div>
      </div>
      <div className="flex flex-col px-6 mt-4 w-full">
        {items.map((item, index) => (
          <div key={index} className="flex flex-col w-full">
            <div className="flex flex-wrap gap-2 items-center py-1 w-full bg-neutral-50">
              <div className="flex gap-0.5 items-start self-stretch my-auto text-xl text-center uppercase whitespace-nowrap text-slate-500">
                <div className="flex shrink-0 self-stretch w-px h-4" />
                <img loading="lazy" src="https://cdn.builder.io/api/v1/image/assets/7fd5ec0079584b17bc43d5c78eb1268d/26d4b28b6d2c04d5812a6b3dd7a4065c4b556953a5585f808266965347d813f8?apiKey=7fd5ec0079584b17bc43d5c78eb1268d&" alt="" className="object-contain shrink-0 w-4 aspect-square" />
                <div className="px-0.5 py-1 w-4"></div>
              </div>
              <div className="flex flex-wrap flex-1 shrink gap-1.5 self-stretch my-auto basis-0 min-w-[240px]">
                <div className="self-start text-sm text-[NeutralForeground1.Rest]">
                  {item.fileName} ({item.count})
                </div>
                <div className="flex items-start h-full text-xs leading-4 whitespace-nowrap text-[NeutralForeground3.Rest]">
                  <div className="opacity-80">source</div>
                </div>
              </div>
            </div>
            {item.messages.map((message, msgIndex) => (
              <div key={msgIndex} className="flex flex-wrap gap-2 items-center py-1 pl-5 mt-3 w-full bg-neutral-50">
                <div className={`flex gap-0.5 self-stretch my-auto text-base ${type === 'error' ? 'text-red-700' : 'text-yellow-600'} uppercase whitespace-nowrap`}>
                  <img loading="lazy" src="https://cdn.builder.io/api/v1/image/assets/7fd5ec0079584b17bc43d5c78eb1268d/e8fd033417e1c55f959bd46211a6151e246ac97ada9c2710f081b7a58bf855e3?apiKey=7fd5ec0079584b17bc43d5c78eb1268d&" alt="" className="object-contain shrink-0 w-px aspect-[0.06]" />
                  <div className="self-start w-4 min-h-[16px]"></div>
                </div>
                <div className="flex flex-wrap flex-1 shrink gap-1.5 self-stretch my-auto basis-0 min-w-[240px]">
                  <div className="self-start text-sm text-[NeutralForeground1.Rest]">
                    {message.message}
                  </div>
                  <div className="flex items-start h-full text-xs leading-4 text-[NeutralForeground3.Rest]">
                    <div className="opacity-80">{message.location}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};